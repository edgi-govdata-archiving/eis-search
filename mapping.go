package main

import (
	"github.com/blevesearch/bleve"
	"github.com/blevesearch/bleve/analysis/analyzer/keyword"
	"github.com/blevesearch/bleve/analysis/lang/en"
	"github.com/blevesearch/bleve/mapping"
)

func buildIndexMapping() (mapping.IndexMapping, error) {

	// a generic reusable mapping for english text
	englishTextFieldMapping := bleve.NewTextFieldMapping()
	englishTextFieldMapping.Analyzer = en.AnalyzerName
	dontStoreMeFieldMapping := bleve.NewTextFieldMapping()
	dontStoreMeFieldMapping.Store = false
	dontStoreMeFieldMapping.IncludeInAll = false
	dontStoreMeFieldMapping.IncludeTermVectors = false
	dontStoreMeFieldMapping.Index = false
	// a generic reusable mapping for keyword text
	keywordFieldMapping := bleve.NewTextFieldMapping()
	keywordFieldMapping.Analyzer = keyword.Name

	// beerMapping := bleve.NewDocumentMapping()

	// name
	// beerMapping.AddFieldMappingsAt("name", englishTextFieldMapping)

	// description
	// beerMapping.AddFieldMappingsAt("description",
	// 	englishTextFieldMapping)

	// beerMapping.AddFieldMappingsAt("type", keywordFieldMapping)
	// beerMapping.AddFieldMappingsAt("style", keywordFieldMapping)
	// beerMapping.AddFieldMappingsAt("category", keywordFieldMapping)

	// breweryMapping := bleve.NewDocumentMapping()
	// breweryMapping.AddFieldMappingsAt("name", englishTextFieldMapping)
	// breweryMapping.AddFieldMappingsAt("description", englishTextFieldMapping)

	//**********added
	tableMapping := bleve.NewDocumentMapping()
	tableMapping.AddFieldMappingsAt("title", englishTextFieldMapping)
	tableMapping.AddFieldMappingsAt("EIS Title",
		englishTextFieldMapping)
	//----experiments
	tableMapping.AddFieldMappingsAt("pgTitle", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("sectionTitle", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("numDataRows", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("tableCaption", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("_id", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("pgId", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("numCols", dontStoreMeFieldMapping)
	tableMapping.AddFieldMappingsAt("numHeaderRows", dontStoreMeFieldMapping)
	//**********added

	indexMapping := bleve.NewIndexMapping()
	// indexMapping.AddDocumentMapping("beer", beerMapping)
	// indexMapping.AddDocumentMapping("brewery", breweryMapping)
	//added
	indexMapping.AddDocumentMapping("table", tableMapping)
	//added

	indexMapping.TypeField = "type"
	indexMapping.DefaultAnalyzer = "en"

	return indexMapping, nil
}
