# EIS Document Database Search

This app makes an archive of the EPA's Environmental Impact Statements (EIS) searchable, linking results back to EIS documents on epa.gov

**Try the EIS Search Tool (demo):** https://eis-search.herokuapp.com

#### Notes

* The current version of the web app is configured to make requests as the user types, but does not have any auto-complete functionality, so you may have zero results showing up when you are halfway through typing a given word.
* The database currently used by this tool is a non-updating snapshot of records found on the [EPA's EIS Database](https://cdxnodengn.epa.gov/cdx-enepa-public/action/eis/search)

### Future Enhancements

- [ ] **pagination** (currently you only access the first 10 results in the gui--though the remainder can currently be accessed via the api)
- [ ] **adding facets** to the search index (to help filter results on axes like date range and specific metadata fields such as the geography for which the document is relevant
- [ ] **better text-pre-processing and tokenization tuning**
- [ ] **improved document mappings** to include more relevant metadata fields and with appropriate weighting
- [ ] **add more info to search page**

## For Developers

### Tools used
* The app is written in [go](https://golang.org/)
* The search index is built with [bleve](https://github.com/blevesearch/bleve) (similar to a light-weight elasticsearch and written in golang) using metadata extracted from every reachable EIS url (including text extracted with OCR from attached/associated PDFs)

### Developer setup
1. Install [Go](https://golang.org/dl/), (make sure your GOPATH [ends up in the right PATH profile](https://github.com/alco/gostart#1-how-do-i-start-writing-go-code))

#### To run locally (without cloning):

2. Install this repo's dependencies with `go get github.com/edgi-govdata-archiving/eis-search`, (run this from any directory)
3. `cd` into `$HOME/go/bin` and run `./eis-search`
4. Server is running at http://localhost:8094 (or other port as specified in command line output)

#### To clone & run:

2. Clone this repo into your go directory (typically `$HOME/go/src`)
3. From inside that cloned directory, `go build`. This should make a file called `eis-search`
4. Run: `./eis-search`
5. Server is running at http://localhost:8094 (or other port as specified in command line output)
