package main

import (
	"net/http"
	"fmt"
	"os"
)

func main() {
	containerID, _ := os.Hostname()
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello, world! I'm container: %s. version 0.0.13\n", containerID)
	})

	// never remove this api, it's needed ]to do healthcheck
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "ok")
	})
	http.ListenAndServe(":{{port}}", nil)
}
