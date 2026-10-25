package site

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type contactHarness struct {
	c      *Contact
	now    *atomic.Int64
	cookie *http.Cookie
	token  string
}

func newContactHarness(t *testing.T, send func(context.Context, M, string, string) bool) *contactHarness {
	t.Helper()
	now := &atomic.Int64{}
	now.Store(time.Now().Unix())
	c := NewContact(ContactConfig{Key: "test-key", SiteKey: "test-site", Secret: "test-secret", StateDir: t.TempDir(), Now: func() time.Time { return time.Unix(now.Load(), 0) }, Verify: func(context.Context, string, string) bool { return true }, Send: send})
	w := httptest.NewRecorder()
	v, _ := c.Handle(w, httptest.NewRequest("GET", "http://example.test/de/mitmachen", nil), "/de/mitmachen")
	if v["status"] != 200 {
		t.Fatal(v)
	}
	h := &contactHarness{c, now, w.Result().Cookies()[0], str(v["token"])}
	now.Add(3)
	return h
}
func (h *contactHarness) post(fields url.Values) (M, *httptest.ResponseRecorder, bool) {
	if fields == nil {
		fields = url.Values{"token": {h.token}, "name": {"Test"}, "email": {"test@example.test"}, "nachricht": {"Test message"}, "cf-turnstile-response": {"test-token"}}
	}
	r := httptest.NewRequest("POST", "http://example.test/de/mitmachen", strings.NewReader(fields.Encode()))
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	r.AddCookie(h.cookie)
	r.RemoteAddr = "203.0.113.4:1234"
	w := httptest.NewRecorder()
	v, done := h.c.Handle(w, r, "/de/mitmachen")
	return v, w, done
}
func TestContactConcurrentTokenConsumption(t *testing.T) {
	var sends atomic.Int32
	h := newContactHarness(t, func(context.Context, M, string, string) bool {
		sends.Add(1)
		time.Sleep(25 * time.Millisecond)
		return true
	})
	var wg sync.WaitGroup
	results := make(chan int, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			v, w, done := h.post(nil)
			if done {
				results <- w.Code
			} else {
				results <- num(v["status"])
			}
		}()
	}
	wg.Wait()
	close(results)
	counts := map[int]int{}
	for s := range results {
		counts[s]++
	}
	if sends.Load() != 1 || counts[303] != 1 || counts[400] != 1 {
		t.Fatalf("sends=%d statuses=%v", sends.Load(), counts)
	}
}
func TestContactRetryKeySurvivesRestart(t *testing.T) {
	var keys []string
	send := func(_ context.Context, _ M, _, key string) bool { keys = append(keys, key); return false }
	h := newContactHarness(t, send)
	v, _, _ := h.post(nil)
	if v["status"] != 502 {
		t.Fatal(v)
	}
	h.c = NewContact(h.c.config)
	v, _, _ = h.post(nil)
	if v["status"] != 502 || len(keys) != 2 || keys[0] != keys[1] || len(keys[0]) != 32 {
		t.Fatalf("%v %v", v, keys)
	}
}
func TestContactExpiryValidationCooldownAndLimit(t *testing.T) {
	t.Run("expired", func(t *testing.T) {
		h := newContactHarness(t, func(context.Context, M, string, string) bool { t.Fatal("sent"); return true })
		h.now.Add(7201)
		v, _, _ := h.post(nil)
		if v["status"] != 400 {
			t.Fatal(v)
		}
	})
	t.Run("honeypot", func(t *testing.T) {
		h := newContactHarness(t, nil)
		v, w, _ := h.post(url.Values{"token": {h.token}, "website": {"spam"}})
		if v["status"] != 429 || w.Header().Get("Retry-After") != "60" {
			t.Fatal(v)
		}
	})
	t.Run("validation", func(t *testing.T) {
		h := newContactHarness(t, nil)
		v, _, _ := h.post(url.Values{"token": {h.token}, "email": {"bad"}, "nachricht": {""}})
		if v["status"] != 422 || len(asMap(v["fehler"])) != 2 {
			t.Fatal(v)
		}
	})
	t.Run("limit", func(t *testing.T) {
		h := newContactHarness(t, func(context.Context, M, string, string) bool { return false })
		for i := 0; i < 6; i++ {
			v, _, _ := h.post(nil)
			want := 502
			if i == 5 {
				want = 429
			}
			if num(v["status"]) != want {
				t.Fatalf("attempt%d: %v", i, v)
			}
		}
	})
	t.Run("cooldown", func(t *testing.T) {
		h := newContactHarness(t, func(context.Context, M, string, string) bool { return true })
		_, _, done := h.post(nil)
		if !done {
			t.Fatal("no redirect")
		}
		w := httptest.NewRecorder()
		r := httptest.NewRequest("GET", "http://example.test/de/mitmachen", nil)
		r.AddCookie(h.cookie)
		v, _ := h.c.Handle(w, r, "/de/mitmachen")
		if v["erfolg"] != true {
			t.Fatal(v)
		}
		h.token = str(v["token"])
		h.now.Add(3)
		v, _, _ = h.post(nil)
		if v["status"] != 429 {
			t.Fatal(v)
		}
	})
}
func TestTrustedProxyBoundary(t *testing.T) {
	c := NewContact(ContactConfig{TrustProxy: true})
	for _, tc := range []struct {
		remote, ip string
		secure     bool
	}{{"127.0.0.1:123", "198.51.100.8", true}, {"[::1]:123", "198.51.100.8", true}, {"203.0.113.9:123", "203.0.113.9", false}} {
		r := httptest.NewRequest("GET", "http://example.test", nil)
		r.RemoteAddr = tc.remote
		r.Header.Set("X-Real-IP", "198.51.100.8")
		r.Header.Set("X-Forwarded-Proto", "https")
		if c.clientIP(r) != tc.ip || c.secure(r) != tc.secure {
			t.Fatal(tc)
		}
	}
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }
func TestTurnstileBindsHostnameAndAction(t *testing.T) {
	old := contactClient
	defer func() { contactClient = old }()
	for _, tc := range []struct {
		host, action  string
		success, want bool
	}{{"jackieleven.com", "contact", true, true}, {"www.jackieleven.com", "contact", true, true}, {"evil.test", "contact", true, false}, {"jackieleven.com", "other", true, false}, {"jackieleven.com", "contact", false, false}} {
		contactClient = &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
			b, _ := io.ReadAll(r.Body)
			v, _ := url.ParseQuery(string(b))
			if len(v) != 2 || v.Get("secret") != "secret" || v.Get("response") != "token" {
				t.Fatalf("unexpected verification payload %v", v)
			}
			return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(fmt.Sprintf(`{"success":%t,"hostname":%q,"action":%q}`, tc.success, tc.host, tc.action))), Header: http.Header{}}, nil
		})}
		if got := verifyTurnstile(context.Background(), "token", "secret"); got != tc.want {
			t.Fatal(tc)
		}
	}
}
func TestPHPQueryOverwriteSemantics(t *testing.T) {
	for _, tc := range []struct{ q, want string }{{"auswahl=0&auswahl=2", "2"}, {"auswahl=0&auswahl[]=2", ""}, {"auswahl[]=0&auswahl=2", "2"}} {
		if got := phpQuery(tc.q).Get("auswahl"); got != tc.want {
			t.Fatalf("%s: %q", tc.q, got)
		}
	}
}

func TestContactEmailAndHoneypotParity(t *testing.T) {
	for _, tc := range []struct {
		email string
		valid bool
	}{{"x@localhost", false}, {"ü@example.com", false}, {"a@-x.com", false}, {"a@x-.com", false}, {"\"foo\"@example.com", true}, {"\"a b\"@example.com", false}, {"a@x.123", false}, {"a@[127.0.0.1]", true}, {"a..b@example.com", false}, {"a+b@example.com", true}} {
		if validContactEmail(tc.email) != tc.valid {
			t.Error(tc)
		}
	}
	for _, tc := range []struct {
		raw    string
		filled bool
	}{{"website[]=bot", true}, {"website[x]=bot", true}, {"website[]=", true}, {"website=0", false}, {"website[x]=bot&website=", false}, {"website=&website[x]=bot", true}} {
		if honeypotFilled(tc.raw) != tc.filled {
			t.Error(tc)
		}
	}
}
func TestContactRejectsTrailingUpstreamJSON(t *testing.T) {
	for _, body := range []string{`{"id":"accepted"}garbage`, `{"id":"accepted"}{}`} {
		var v M
		if decodeContactJSON(strings.NewReader(body), &v) == nil {
			t.Errorf("accepted malformed upstream response %q", body)
		}
	}
	var v M
	if decodeContactJSON(strings.NewReader(`{"id":"accepted"} `), &v) != nil {
		t.Fatal("rejected valid response")
	}
}

func TestContactEmailPHPFixture(t *testing.T) {
	path := os.Getenv("JACKIE_PHP_EMAIL_FIXTURE")
	if path == "" {
		path = "testdata/email-validation.json"
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var cases []struct {
		Email string
		Valid bool
	}
	if err = json.Unmarshal(b, &cases); err != nil {
		t.Fatal(err)
	}
	for _, tc := range cases {
		if validContactEmail(tc.Email) != tc.Valid {
			t.Errorf("%q: want%t", tc.Email, tc.Valid)
		}
	}
}

func TestContactHonorsFormContentType(t *testing.T) {
	h := newContactHarness(t, func(context.Context, M, string, string) bool { return false })
	values := url.Values{"token": {h.token}, "email": {"test@example.test"}, "nachricht": {"message"}}
	r := httptest.NewRequest("POST", "http://example.test/de/mitmachen", strings.NewReader(values.Encode()))
	r.Header.Set("Content-Type", "text/plain")
	r.AddCookie(h.cookie)
	v, _ := h.c.Handle(httptest.NewRecorder(), r, "/de/mitmachen")
	if v["status"] != 400 {
		t.Fatal(v)
	}
	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	for k, vs := range values {
		writer.WriteField(k, vs[0])
	}
	writer.Close()
	r = httptest.NewRequest("POST", "http://example.test/de/mitmachen", &body)
	r.Header.Set("Content-Type", writer.FormDataContentType())
	r.AddCookie(h.cookie)
	v, _ = h.c.Handle(httptest.NewRecorder(), r, "/de/mitmachen")
	if v["status"] != 502 {
		t.Fatal(v)
	}
	payload := contactPayload(M{"name": "0", "email": "test@example.test", "nachricht": "message"})
	if !strings.Contains(str(payload["text"]), "Name: —") {
		t.Fatal(payload)
	}
}

func TestContactCacheControlMatchesPHPSession(t *testing.T) {
	c := NewContact(ContactConfig{StateDir: t.TempDir()})
	for _, method := range []string{"GET", "POST"} {
		r := httptest.NewRequest(method, "http://example.test/de/mitmachen", nil)
		w := httptest.NewRecorder()
		c.Handle(w, r, "/de/mitmachen")
		if got := w.Header().Get("Cache-Control"); got != "no-store, no-cache, must-revalidate" {
			t.Errorf("%s Cache-Control=%q", method, got)
		}
	}
}
