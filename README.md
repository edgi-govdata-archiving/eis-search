# EIS Document Database Search

### About

This app makes an archive of the EPA's Environmental Impact Statements (EIS) searchable.

The search index is built with [bleve](https://github.com/blevesearch/bleve) (similar to a light-weight elasticsearch and written in golang) using metadata extracted from every reachable EIS url (including text extracted with OCR from attached/associated PDFs)

### Future Enhancements

- [ ] **pagination** (currently you only access the first 10 results in the gui--though the remainder can currently be accessed via the api)
- [ ] **adding facets** to the search index (to help filter results on axes like date range and specific metadata fields such as the geography for which the document is relevant
- [ ] **better text-pre-processing and tokenization tuning** 
- [ ] **improved document mappings** to include more relevant metadata fields and with appropriate weighting

#### Notes

The current version of the web app is configured to make requests as the user types, but does not have any auto-complete functionality so you may have zero results showing up when you are halfway through typing a given word.