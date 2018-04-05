package main

import (
	"net/http"

	"github.com/gorilla/mux"
)

func staticFileRouter() *mux.Router {
	r := mux.NewRouter()
	r.StrictSlash(true)

	// static
	r.PathPrefix("/static/").Handler(http.StripPrefix("/static/",
		myFileHandler{http.FileServer(http.Dir(*staticPath))}))

	// application pages
	appPages := []string{
		"/overview",
		"/search",
	}

	for _, p := range appPages {
		// if you try to use index.html it will redirect...poorly
		r.PathPrefix(p).Handler(RewriteURL("/",
			http.FileServer(http.Dir(*staticPath))))
	}

	r.Handle("/", http.RedirectHandler("/static/index.html", 302))

	return r
}

type myFileHandler struct {
	h http.Handler
}

func (mfh myFileHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if *staticEtag != "" {
		w.Header().Set("Etag", *staticEtag)
	}
	mfh.h.ServeHTTP(w, r)
}

func RewriteURL(to string, h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		r.URL.Path = to
		h.ServeHTTP(w, r)
	})
}

func muxVariableLookup(req *http.Request, name string) string {
	return mux.Vars(req)[name]
}

func docIDLookup(req *http.Request) string {
	return muxVariableLookup(req, "docID")
}
