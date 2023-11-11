# Syncing Excel & Vocabs

## Excel to RDF

The script **_dump_codelists_to_vocabs.py** dumps all the code lists in a given Excel file's VALIDATION_DICTONARY sheet to SKOS RDF files in a given dictionary.

This script has been run and produced a result that is the basis for conversions from RDF to Excel.

_**NOTE:** Having been run to generate SKOS RDF from the previous template, this script should not be run again and is retained for reference only_.

## RDF to Excel

The script **make_sheet_from_vocabs.py** creates an Excel workbook containing a single worksheet called VALIDATION_DICTIONARY that contains codelists from all the vocabularies in SKOS RDF in a given directory.

This script should be used to regenerate codelists whenever vocabularies are updated.

See the script itself for usage notes (top of the file).

New Concepts may be added to existing vocabularies and new vocabularies may be added to the directory and these will generate new codelists.

New Concepts and vocabularies must follow the format of existing ones which is the same as all GSQ Cocnepts and vocabs however these used here must also contain a `skos:notation` property for each that supplies the code for the codelist, e.g., for the vocabulary Soil Colour:

```
cs:
    a skos:ConceptScheme ;
    skos:definition "Soil Colour"@en ;
    skos:hasTopConcept
        ...
        :purple ,
        :red ,
        :white ,
        :yellow ;
    ...
    skos:notation "SOIL_COLOUR" ;
    skos:prefLabel "Soil Colour"@en ;
    ...;
.
```

You can see standard vocabulary properties and also `skos:notation "SOIL_COLOUR" ;` which means this vocab will generate a codlists with the heading `SOIL_COLOUR`.

Within that vocab, here is a Concept:

```
:purple
    a skos:Concept ;
    ...
    skos:notation "PURPLE" ;
    skos:prefLabel "purple"@en ;
    skos:topConceptOf cs: ;
.
```

This will become `PURPLE` within the `SOIL_COLOUR`.

## Validation using vocabs

The script **combine_concepts_for_validation.py** reads all the vocabs in a given directory and extracts just the triples indicating Concepts are within particular Concept Schemes: `{CONCEPT_IRI} skos:inScheme {CONCEPT_CSCHEM_IRI}`. These are then used in SHACL validation to check that any IRI quotes in data that should come from a vocab really does.

The script outputs a file called **concepts-combined.ttl** and this is then, in turn, combined with data to be validated. 

This script should be run whenever vocabularies are updated.