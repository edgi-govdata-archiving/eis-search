package main

import (
	"encoding/json"
	_ "expvar"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"runtime/pprof"
	"strings"
	"time"

	"github.com/blevesearch/bleve"
	_ "github.com/blevesearch/bleve/config"
	bleveHttp "github.com/blevesearch/bleve/http"
)

var batchSize = flag.Int("batchSize", 100, "batch size for indexing")
var bindAddr = flag.String("addr", "8094", "http listen address")

//var jsonDir = flag.String("jsonDir", "data/", "json directory")
// var jsonDir = flag.String("jsonDir", "/Volumes/LaCie/wikitables/bleve/", "json directory")
var jsonDir = flag.String("jsonDir", "/Volumes/LaCie/eis/json_files/", "json directory")
var indexPath = flag.String("index", "doc-search.bleve", "index path")
var staticEtag = flag.String("staticEtag", "", "A static etag value.")
var staticPath = flag.String("static", "static/", "Path to the static content")
var cpuprofile = flag.String("cpuprofile", "", "write cpu profile to file")
var memprofile = flag.String("memprofile", "", "write mem profile to file")

func main() {
	port := os.Getenv("PORT")
	if port != "" {
		*bindAddr = port
	}

	flag.Parse()

	log.Printf("GOMAXPROCS: %d", runtime.GOMAXPROCS(-1))

	if *cpuprofile != "" {
		f, err := os.Create(*cpuprofile)
		if err != nil {
			log.Fatal(err)
		}
		pprof.StartCPUProfile(f)
	}

	// open the index
	docIndex, err := bleve.Open(*indexPath)
	if err == bleve.ErrorIndexPathDoesNotExist {
		log.Printf("Creating new index...")
		// create a mapping
		indexMapping, err := buildIndexMapping()
		if err != nil {
			log.Fatal(err)
		}
		docIndex, err = bleve.New(*indexPath, indexMapping)
		if err != nil {
			log.Fatal(err)
		}

		// index data in the background
		go func() {
			err = indexDocs(docIndex)
			if err != nil {
				log.Fatal(err)
			}
			pprof.StopCPUProfile()
			if *memprofile != "" {
				f, err := os.Create(*memprofile)
				if err != nil {
					log.Fatal(err)
				}
				pprof.WriteHeapProfile(f)
				f.Close()
			}
		}()
	} else if err != nil {
		log.Fatal(err)
	} else {
		log.Printf("Opening existing index...")
	}

	// create a router to serve static files
	router := staticFileRouter()

	// add the API
	bleveHttp.RegisterIndexName("doc", docIndex)
	searchHandler := bleveHttp.NewSearchHandler("doc")
	router.Handle("/api/search", searchHandler).Methods("POST")
	listFieldsHandler := bleveHttp.NewListFieldsHandler("doc")
	router.Handle("/api/fields", listFieldsHandler).Methods("GET")

	debugHandler := bleveHttp.NewDebugDocumentHandler("doc")
	debugHandler.DocIDLookup = docIDLookup
	router.Handle("/api/debug/{docID}", debugHandler).Methods("GET")

	// start the HTTP server
	http.Handle("/", router)
	log.Printf("Listening on %v", ":"+*bindAddr)
	log.Fatal(http.ListenAndServe(":"+*bindAddr, nil))
}

func indexDocs(i bleve.Index) error {
	// open the directory
	dirEntries, err := ioutil.ReadDir(*jsonDir)
	if err != nil {
		return err
	}

	// walk the directory entries for indexing
	log.Printf("Indexing...")
	count := 0
	startTime := time.Now()
	batch := i.NewBatch()
	batchCount := 0
	for _, dirEntry := range dirEntries {
		filename := dirEntry.Name()
		// read bytes
		jsonBytes, err := ioutil.ReadFile(*jsonDir + "/" + filename)
		if err != nil {
			return err
		}
		// parse bytes as json
		pieces := strings.Split(filename, ".")
		lastIndex := len(pieces) - 1
		if pieces[lastIndex] == "json" {
			var jsonDoc interface{}
			err = json.Unmarshal(jsonBytes, &jsonDoc)
			if err != nil {
				fmt.Println(filename)
				return err
			}
			ext := filepath.Ext(filename)
			docID := filename[:(len(filename) - len(ext))]
			batch.Index(docID, jsonDoc)
			batchCount++

			if batchCount >= *batchSize {
				err = i.Batch(batch)
				if err != nil {
					return err
				}
				batch = i.NewBatch()
				batchCount = 0
			}
			count++
			if count%1000 == 0 {
				indexDuration := time.Since(startTime)
				indexDurationSeconds := float64(indexDuration) / float64(time.Second)
				timePerDoc := float64(indexDuration) / float64(count)
				log.Printf("Indexed %d documents, in %.2fs (average %.2fms/doc)", count, indexDurationSeconds, timePerDoc/float64(time.Millisecond))
			}

		}

	}
	// flush the last batch
	if batchCount > 0 {
		err = i.Batch(batch)
		if err != nil {
			log.Fatal(err)
		}
	}
	indexDuration := time.Since(startTime)
	indexDurationSeconds := float64(indexDuration) / float64(time.Second)
	timePerDoc := float64(indexDuration) / float64(count)
	log.Printf("Indexed %d documents, in %.2fs (average %.2fms/doc)", count, indexDurationSeconds, timePerDoc/float64(time.Millisecond))
	return nil
}
