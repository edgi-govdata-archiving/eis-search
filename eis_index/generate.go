package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/puerkitobio/goquery"
	"github.com/sirupsen/logrus"
)

var (
	log          = logrus.New()
	start        = 20000
	pagesRegex   = regexp.MustCompile(`\((\w*)\spp`)
	url          = "https://cdxnodengn.epa.gov/cdx-enepa-II/public/action/eis/details"
	ErrInvalidID = fmt.Errorf("invalid statement ID")
)

func main() {
	// statements :=
	eis, err := NewEpaEIS(260927)
	if err != nil {
		panic(err)
	}

	data, err := json.MarshalIndent(eis, "", "  ")
	if err != nil {
		panic(err)
	}

}

// NewEpaEIS attempts to fetch an EIS statement from epa.gov
func NewEpaEIS(id int) (*EIS, error) {
	stmt := &EIS{
		ID:     id,
		Source: "EPA",
		URL:    fmt.Sprintf("%s?eisId=%d", url, id),
	}

	res, err := http.Get(stmt.URL)
	if err != nil {
		return nil, err
	}
	if res.StatusCode != 200 {
		return nil, ErrInvalidID
	}
	fmt.Println(res.StatusCode)

	doc, err := goquery.NewDocumentFromResponse(res)
	if err != nil {
		return nil, err
	}

	// remove titles
	doc.Find(`.pane-content .fieldset-wrapper .form-item h4`).Remove()

	doc.Find(`.pane-content .fieldset-wrapper .form-item`).Each(func(i int, el *goquery.Selection) {
		str := strings.TrimSpace(el.Text())
		switch i {
		case 0:
			stmt.Title = str
		case 1:
			stmt.EISNumber = str
		case 2:
			stmt.DocType = str
		case 3:
			stmt.FederalRegistrarDate = str
		case 4:
			stmt.ReviewCloseDate = str
		case 5:
			stmt.NoticeDate = str
		case 6:
			stmt.Notice = str
		case 7:
			stmt.SupplementalInfo = str
		case 8:
			stmt.Website = str
		case 9:
			stmt.EPACommentLetterDate = str
		case 10:
			stmt.State = str
		case 11:
			stmt.LeadAgency = str
		case 12:
			stmt.ContactName = str
		case 13:
			stmt.ContactPhone = str
		case 14:
			stmt.Rating = str
		}
	})

	doc.Find("#links ~ p").Each(func(i int, el *goquery.Selection) {
		URL, _ := el.ChildrenFiltered("a").Attr("href")
		doc := &Document{
			URL:   URL,
			Title: el.ChildrenFiltered("a").Text(),
		}

		if matches := pagesRegex.FindStringSubmatch(el.Text()); len(matches) > 0 {
			doc.Pages = matches[1]
		}

		if doc.Title != "" {
			stmt.Documents = append(stmt.Documents, doc)
		}
	})

	return stmt, nil
}

// EIS is a model of an Environmental Impact Statement
type EIS struct {
	ID                   int
	Source               string
	URL                  string
	Title                string
	EISNumber            string
	DocType              string
	FederalRegistrarDate string
	ReviewCloseDate      string
	NoticeDate           string
	Notice               string
	SupplementalInfo     string
	Website              string
	EPACommentLetterDate string
	State                string
	LeadAgency           string
	ContactName          string
	ContactPhone         string
	Rating               string
	Documents            []*Document
}

// Document is an attached document to an EIS statement
type Document struct {
	Title string
	URL   string
	Pages string
	Size  string
}
