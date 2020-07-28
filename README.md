# **IMPORTANT! We've moved development of this repo to the `main` branch. You will not be able to merge changes into `master`.**

## **UPDATING LOCAL CLONES**

(via [this link](https://www.hanselman.com/blog/EasilyRenameYourGitDefaultBranchFromMasterToMain.aspx), thanks!)

If you have a local clone, you can update and change your default branch with the steps below.

```sh
git checkout master
git branch -m master main
git fetch
git branch --unset-upstream
git branch -u origin/main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
```

The above steps accomplish:

1. Go to the master branch
2. Rename master to main locally
3. Get the latest commits from the server
4. Remove the link to origin/master
5. Add a link to origin/main
6. Update the default branch to be origin/main

[![Code of Conduct](https://img.shields.io/badge/%E2%9D%A4-code%20of%20conduct-blue.svg?style=flat)](https://github.com/edgi-govdata-archiving/overview/blob/master/CONDUCT.md)

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

## License & Copyright

Copyright (C) 2019 Environmental Data and Governance Initiative (EDGI)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [`LICENSE`](/LICENSE) file for details.
