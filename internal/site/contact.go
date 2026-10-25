package site

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"mime"
	"mime/multipart"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
	"time"
	"unicode/utf8"
)

// ContactConfig allows deterministic tests without contacting either external
// service. Production credentials are supplied by the process environment only.
type ContactConfig struct {
	Key, SiteKey, Secret, StateDir string
	CookiePath                     string
	TrustProxy                     bool
	Now                            func() time.Time
	Verify                         func(context.Context, string, string) bool
	Send                           func(context.Context, M, string, string) bool
}
type Contact struct{ config ContactConfig }
type contactForm struct {
	Created  int64             `json:"created"`
	Attempts map[string]string `json:"attempts,omitempty"`
}
type contactSession struct {
	Forms    map[string]*contactForm `json:"forms"`
	Order    []string                `json:"order"`
	LastSent int64                   `json:"last_sent,omitempty"`
	Success  bool                    `json:"success,omitempty"`
	Updated  int64                   `json:"updated"`
}

var sessionIDPattern = regexp.MustCompile(`^[a-f0-9]{48}$`)

func ContactConfigFromEnv() ContactConfig {
	return ContactConfig{Key: os.Getenv("JACKIE_RESEND_API_KEY"), SiteKey: os.Getenv("JACKIE_TURNSTILE_SITEKEY"), Secret: os.Getenv("JACKIE_TURNSTILE_SECRET"), StateDir: os.Getenv("JACKIE_CONTACT_STATE_DIR")}
}
func NewContact(config ContactConfig) *Contact {
	if config.CookiePath == "" {
		config.CookiePath = "/"
	}
	if config.StateDir == "" {
		config.StateDir = filepath.Join(os.TempDir(), "jackieleven-contact-go")
	}
	if config.Now == nil {
		config.Now = time.Now
	}
	if config.Verify == nil {
		config.Verify = verifyTurnstile
	}
	if config.Send == nil {
		config.Send = sendContact
	}
	return &Contact{config}
}
func randomHex(n int) (string, error) {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
func (c *Contact) trustedProxy(r *http.Request) bool {
	if !c.config.TrustProxy {
		return false
	}
	h, _, e := net.SplitHostPort(r.RemoteAddr)
	if e != nil {
		h = r.RemoteAddr
	}
	ip := net.ParseIP(h)
	return ip != nil && ip.IsLoopback()
}
func (c *Contact) secure(r *http.Request) bool {
	return r.TLS != nil || (c.trustedProxy(r) && r.Header.Get("X-Forwarded-Proto") == "https")
}
func (c *Contact) clientIP(r *http.Request) string {
	if c.trustedProxy(r) {
		if ip := net.ParseIP(strings.TrimSpace(r.Header.Get("X-Real-IP"))); ip != nil {
			return ip.String()
		}
	}
	h, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil {
		return h
	}
	if r.RemoteAddr != "" {
		return r.RemoteAddr
	}
	return "unknown"
}
func lockFile(path string, create bool) (*os.File, error) {
	flags := os.O_RDWR
	if create {
		flags |= os.O_CREATE
	}
	f, err := os.OpenFile(path, flags, 0600)
	if err != nil {
		return nil, err
	}
	if err = syscall.Flock(int(f.Fd()), syscall.LOCK_EX); err != nil {
		f.Close()
		return nil, err
	}
	return f, nil
}
func closeLocked(f *os.File) { syscall.Flock(int(f.Fd()), syscall.LOCK_UN); f.Close() }
func writeState(f *os.File, v any) error {
	b, err := json.Marshal(v)
	if err != nil {
		return err
	}
	if _, err = f.Seek(0, io.SeekStart); err != nil {
		return err
	}
	if _, err = f.Write(b); err != nil {
		return err
	}
	if err = f.Truncate(int64(len(b))); err != nil {
		return err
	}
	return f.Sync()
}
func (c *Contact) session(w http.ResponseWriter, r *http.Request) (*os.File, *contactSession, error) {
	dir := filepath.Join(c.config.StateDir, "sessions")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return nil, nil, err
	}
	var f *os.File
	cookie, err := r.Cookie("jackie_contact")
	if err == nil && sessionIDPattern.MatchString(cookie.Value) {
		f, err = lockFile(filepath.Join(dir, cookie.Value+".json"), false)
		if err != nil && !errors.Is(err, os.ErrNotExist) {
			return nil, nil, err
		}
	}
	if f == nil {
		id, err := randomHex(24)
		if err != nil {
			return nil, nil, err
		}
		f, err = lockFile(filepath.Join(dir, id+".json"), true)
		if err != nil {
			return nil, nil, err
		}
		http.SetCookie(w, &http.Cookie{Name: "jackie_contact", Value: id, Path: c.config.CookiePath, HttpOnly: true, Secure: c.secure(r), SameSite: http.SameSiteLaxMode})
	}
	s := &contactSession{Forms: map[string]*contactForm{}}
	b, err := io.ReadAll(io.LimitReader(f, 1<<20))
	if err != nil {
		closeLocked(f)
		return nil, nil, err
	}
	if len(b) > 0 {
		if err = json.Unmarshal(b, s); err != nil {
			closeLocked(f)
			return nil, nil, err
		}
	}
	if s.Forms == nil {
		s.Forms = map[string]*contactForm{}
	}
	return f, s, nil
}
func (c *Contact) allowAttempt(ip string, now int64) (bool, error) {
	if err := os.MkdirAll(c.config.StateDir, 0700); err != nil {
		return false, err
	}
	sum := sha256.Sum256([]byte(time.Unix(now, 0).UTC().Format("2006-01-02") + ":" + ip))
	path := filepath.Join(c.config.StateDir, hex.EncodeToString(sum[:])+".json")
	f, err := lockFile(path, true)
	if err != nil {
		return false, err
	}
	defer closeLocked(f)
	var old []int64
	b, err := io.ReadAll(io.LimitReader(f, 1<<20))
	if err != nil {
		return false, err
	}
	if len(b) > 0 && json.Unmarshal(b, &old) != nil {
		return false, errors.New("invalid limiter state")
	}
	times := []int64{}
	for _, t := range old {
		if t > now-3600 {
			times = append(times, t)
		}
	}
	if len(times) >= 5 {
		return false, nil
	}
	times = append(times, now)
	if err = writeState(f, times); err != nil {
		return false, err
	}
	return true, nil
}
func (c *Contact) cleanOldState(now int64) {
	for _, dir := range []string{c.config.StateDir, filepath.Join(c.config.StateDir, "sessions")} {
		entries, err := os.ReadDir(dir)
		if err != nil {
			continue
		}
		for _, e := range entries {
			if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
				continue
			}
			info, err := e.Info()
			if err == nil && info.ModTime().Unix() < now-172800 {
				f, err := os.OpenFile(filepath.Join(dir, e.Name()), os.O_RDWR, 0)
				if err != nil {
					continue
				}
				if syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB) == nil {
					os.Remove(filepath.Join(dir, e.Name()))
					syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
				}
				f.Close()
			}
		}
	}
}
func contactFields(v url.Values) M {
	return M{"name": mdTrim(v.Get("name")), "email": mdTrim(v.Get("email")), "nachricht": mdTrim(v.Get("nachricht"))}
}
func validateContact(f M) M {
	out := M{}
	name, email, msg := str(f["name"]), str(f["email"]), str(f["nachricht"])
	badName := utf8.RuneCountInString(name) > 120
	for _, r := range name {
		if r < 32 {
			badName = true
		}
	}
	if badName {
		out["name"] = "name"
	}
	if !validContactEmail(email) {
		out["email"] = "email"
	}

	if msg == "" || utf8.RuneCountInString(msg) > 10000 || !utf8.ValidString(msg) || strings.ContainsRune(msg, 0) {
		out["nachricht"] = "nachricht"
	}
	return out
}
func contactPayload(f M) M {
	name := str(f["name"])
	if !truth(name) {
		name = "—"
	}
	return M{"from": "Jackie Leven · Hommage <jackieleven@unpubli.sh>", "to": []string{"stefan@jackieleven.com"}, "reply_to": f["email"], "subject": "Nachricht zur Jackie-Leven-Hommage", "text": "Nachricht über das Mitmachen-Formular\n\nName: " + name + "\nE-Mail: " + str(f["email"]) + "\n\n" + str(f["nachricht"])}
}

// Handle serializes a session for the entire verification/send transaction. The
// persisted token+payload key survives timeouts and process restarts. No message
// body, email address or visitor IP is persisted in session files.
func (c *Contact) Handle(w http.ResponseWriter, r *http.Request, action string) (M, bool) {
	w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate")
	w.Header().Set("X-Robots-Tag", "noindex")
	now := c.config.Now().Unix()
	ready := c.config.Key != "" && c.config.SiteKey != "" && c.config.Secret != ""
	v := M{"felder": M{"name": "", "email": "", "nachricht": ""}, "fehler": M{}, "global": nil, "status": 200, "erfolg": false, "token": "", "bereit": ready, "turnstile_sitekey": c.config.SiteKey}
	fail := func(status int, msg string) { v["status"] = status; v["global"] = msg }
	f, s, err := c.session(w, r)
	if err != nil {
		fail(503, "versand")
		return v, false
	}
	defer closeLocked(f)
	v["erfolg"] = s.Success
	s.Success = false
	token := ""
	if r.Method == http.MethodPost {
		v["erfolg"] = false
		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 128<<10))
		if err != nil {
			fail(413, "nachricht")
		} else {
			formBody := contactFormBody(body, r.Header.Get("Content-Type"))
			post := parseFormValues(formBody)
			fields := contactFields(post)
			v["felder"] = fields
			token = post.Get("token")
			form := s.Forms[token]
			switch {
			case form == nil || form.Created < now-7200:
				fail(400, "sitzung")
			case honeypotFilled(formBody) || now-form.Created < 2 || now-s.LastSent < 60:
				fail(429, "warten")
			default:
				validation := validateContact(fields)
				v["fehler"] = validation
				if len(validation) > 0 {
					v["status"] = 422
				} else if !ready {
					fail(503, "konfiguration")
				} else {
					allowed, err := c.allowAttempt(c.clientIP(r), now)
					switch {
					case err != nil:
						fail(503, "versand")
					case !allowed:
						fail(429, "warten")
					case !c.config.Verify(r.Context(), post.Get("cf-turnstile-response"), c.config.Secret):
						fail(422, "pruefung")
					default:
						payloadJSON, _ := json.Marshal(fields)
						digest := sha256.Sum256(payloadJSON)
						hash := hex.EncodeToString(digest[:])
						if form.Attempts == nil {
							form.Attempts = map[string]string{}
						}
						key := form.Attempts[hash]
						if key == "" {
							key, err = randomHex(16)
							if err != nil {
								fail(503, "versand")
								break
							}
							form.Attempts[hash] = key
						}
						s.Updated = now
						if err = writeState(f, s); err != nil {
							fail(503, "versand")
							break
						}
						if !c.config.Send(r.Context(), contactPayload(fields), c.config.Key, key) {
							fail(502, "versand")
						} else {
							delete(s.Forms, token)
							s.LastSent = now
							s.Success = true
							if err = writeState(f, s); err != nil {
								fail(503, "versand")
								break
							}
							w.Header().Set("Location", action+"#nachricht")
							w.WriteHeader(303)
							return v, true
						}
					}
				}
			}
		}
	}
	// Keep at most seven older forms plus the current one, in insertion order.
	order := []string{}
	for _, id := range s.Order {
		if form := s.Forms[id]; form != nil && form.Created >= now-7200 {
			order = append(order, id)
		} else {
			delete(s.Forms, id)
		}
	}
	if len(order) > 7 {
		for _, id := range order[:len(order)-7] {
			delete(s.Forms, id)
		}
		order = order[len(order)-7:]
	}
	if s.Forms[token] == nil {
		token, err = randomHex(24)
		if err != nil {
			fail(503, "versand")
			return v, false
		}
		s.Forms[token] = &contactForm{Created: now}
		order = append(order, token)
	}
	s.Order = order
	s.Updated = now
	v["token"] = token
	if err = writeState(f, s); err != nil {
		fail(503, "versand")
	}
	if v["status"] == 429 {
		w.Header().Set("Retry-After", "60")
	}
	c.cleanOldState(now)
	return v, false
}
func verifyTurnstile(ctx context.Context, token, secret string) bool {
	if token == "" || len(token) > 2048 || secret == "" {
		return false
	}
	ctx, cancel := context.WithTimeout(ctx, 8*time.Second)
	defer cancel()
	payload := url.Values{"secret": {secret}, "response": {token}}
	req, err := http.NewRequestWithContext(ctx, "POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify", strings.NewReader(payload.Encode()))
	if err != nil {
		return false
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := contactClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return false
	}
	var result struct {
		Success  bool   `json:"success"`
		Hostname string `json:"hostname"`
		Action   string `json:"action"`
	}
	if decodeContactJSON(resp.Body, &result) != nil {
		return false
	}
	return result.Success && (result.Hostname == "jackieleven.com" || result.Hostname == "www.jackieleven.com") && result.Action == "contact"
}

var contactClient = &http.Client{Transport: &http.Transport{Proxy: http.ProxyFromEnvironment, DialContext: (&net.Dialer{Timeout: 3 * time.Second}).DialContext, TLSHandshakeTimeout: 3 * time.Second, ResponseHeaderTimeout: 20 * time.Second}, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}

func sendContact(ctx context.Context, payload M, key, idempotency string) bool {
	if key == "" {
		return false
	}
	ctx, cancel := context.WithTimeout(ctx, 20*time.Second)
	defer cancel()
	b, err := json.Marshal(payload)
	if err != nil {
		return false
	}
	req, err := http.NewRequestWithContext(ctx, "POST", "https://api.resend.com/emails", bytes.NewReader(b))
	if err != nil {
		return false
	}
	req.Header.Set("Authorization", "Bearer "+key)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", "jackie-contact-"+idempotency)
	resp, err := contactClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return false
	}
	var result struct {
		ID string `json:"id"`
	}
	return decodeContactJSON(resp.Body, &result) == nil && result.ID != ""
}

// parseFormValues preserves the established last-value and scalar/array overwrite behavior for
// this site's scalar controls. Array values are intentionally discarded.
func parseFormValues(raw string) url.Values {
	v := url.Values{}
	for i, part := range strings.Split(raw, "&") {
		if i >= 1000 {
			break
		}
		kv := strings.SplitN(part, "=", 2)
		key, err := url.QueryUnescape(kv[0])
		if err != nil {
			continue
		}
		value := ""
		if len(kv) == 2 {
			value, _ = url.QueryUnescape(kv[1])
		}
		if i := strings.IndexByte(key, '['); i >= 0 {
			v.Del(key[:i])
			continue
		}
		key = strings.NewReplacer(" ", "_", ".", "_").Replace(key)
		v.Set(key, value)
	}
	return v
}

// validContactEmail preserves the established ASCII mailbox validation policy.
// The captured reference cases are retained in testdata/email-validation.json.
func validContactEmail(email string) bool {
	if len(email) > 254 {
		return false
	}
	for _, r := range email {
		if r > 127 || r < 32 || r == 127 {
			return false
		}
	}
	at := strings.LastIndexByte(email, '@')
	if at <= 0 || at > 64 {
		return false
	}
	local, domain := email[:at], email[at+1:]
	if len(domain) == 0 || len(domain) > 253 {
		return false
	}
	if strings.HasPrefix(local, "\"") {
		if len(local) < 2 || local[len(local)-1] != '"' {
			return false
		}
		for i := 1; i < len(local)-1; i++ {
			ch := local[i]
			if ch == '\\' {
				i++
				if i >= len(local)-1 {
					return false
				}
				continue
			}
			if ch == '"' || ch == ' ' || ch == '\\' {
				return false
			}
		}
	} else {
		if local[0] == '.' || local[len(local)-1] == '.' || strings.Contains(local, "..") {
			return false
		}
		for _, ch := range local {
			if !(ch >= 'a' && ch <= 'z' || ch >= 'A' && ch <= 'Z' || ch >= '0' && ch <= '9' || strings.ContainsRune(".!#$%&'*+-/=?^_`{|}~", ch)) {
				return false
			}
		}
	}
	if strings.HasPrefix(domain, "[") && strings.HasSuffix(domain, "]") {
		literal := domain[1 : len(domain)-1]
		if strings.HasPrefix(strings.ToLower(literal), "ipv6:") {
			ip := literal[5:]
			return strings.Contains(ip, ":") && net.ParseIP(ip) != nil
		}
		return !strings.Contains(literal, ":") && net.ParseIP(literal) != nil
	}
	labels := strings.Split(domain, ".")
	if len(labels) < 2 {
		return false
	}
	for _, label := range labels {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return false
		}
		for _, r := range label {
			if !(r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '-') {
				return false
			}
		}
	}
	first := labels[len(labels)-1][0]
	return first >= 'a' && first <= 'z' || first >= 'A' && first <= 'Z'
}

func honeypotFilled(raw string) bool {
	filled := false
	for i, part := range strings.Split(raw, "&") {
		if i >= 1000 {
			break
		}
		kv := strings.SplitN(part, "=", 2)
		key, _ := url.QueryUnescape(kv[0])
		value := ""
		if len(kv) == 2 {
			value, _ = url.QueryUnescape(kv[1])
		}
		if key == "website" {
			filled = truth(value)
		} else if strings.HasPrefix(key, "website[") {
			filled = true
		}
	}
	return filled
}

func decodeContactJSON(body io.Reader, result any) error {
	raw, err := io.ReadAll(io.LimitReader(body, (64<<10)+1))
	if err != nil {
		return err
	}
	if len(raw) > 64<<10 {
		return errors.New("oversized upstream response")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	if err := decoder.Decode(result); err != nil {
		return err
	}
	var trailing any
	if err := decoder.Decode(&trailing); err != io.EOF {
		return errors.New("invalid upstream JSON suffix")
	}
	return nil
}

// Accept POST fields only from the two HTML form encodings. Preserve field order
// so duplicate scalar/array names keep the same overwrite semantics.
func contactFormBody(body []byte, contentType string) string {
	media, params, err := mime.ParseMediaType(contentType)
	if err != nil {
		return ""
	}
	switch media {
	case "application/x-www-form-urlencoded":
		return string(body)
	case "multipart/form-data":
		boundary := params["boundary"]
		if boundary == "" {
			return ""
		}
		reader := multipart.NewReader(bytes.NewReader(body), boundary)
		var fields []string
		for len(fields) < 1000 {
			part, err := reader.NextPart()
			if err == io.EOF {
				break
			}
			if err != nil {
				return ""
			}
			_, disposition, err := mime.ParseMediaType(part.Header.Get("Content-Disposition"))
			if err != nil {
				part.Close()
				continue
			}
			if _, file := disposition["filename"]; file {
				part.Close()
				continue
			}
			name := part.FormName()
			value, err := io.ReadAll(part)
			part.Close()
			if err != nil {
				return ""
			}
			if name != "" {
				fields = append(fields, url.QueryEscape(name)+"="+url.QueryEscape(string(value)))
			}
		}
		return strings.Join(fields, "&")
	default:
		return ""
	}
}
