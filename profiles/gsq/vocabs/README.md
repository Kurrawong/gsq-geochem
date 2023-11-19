# Syncing Excel & Vocabs

This document describes how to keep the set of vocabularies relevant to geochemistry and the VALIDATION_DICTIONARY entries in the Excel template in sync.

1. Excel to Vocabs
   * How the original Excel template (v2)'s VALIDATION_DICTIONARY & UNITS_OF_MEASURE worksheets were used to create vocabulary files
2. Vocabs to Excel
   * How to update the VALIDATION_DICTIONARY & UNITS_OF_MEASURE worksheet in Excel template v3 from vocabulary files
3. Validation using Vocabs
   * How the automated validation scripts use vocabs to validate Excel template v3 content
4. Updating vocabs with Data Supplier's code
   * How to add codes supplied in either the USER_DICTIONARY & USER_UNITS_OF_MEASURE worksheets in a Excel template v3 to the vocabs


## 1. Excel to Vocabs

The script **_excel_codelists_to_vocabs.py** dumps all the code lists in a given Excel file's VALIDATION_DICTONARY sheet to SKOS RDF files in a given dictionary.

the script **_excel_uom_to_vocab.py** dumpes the collections of units in the worksheet UNITS_OF_MEASURE to a single vocabulary.

These scripts have been run and produced results that are the basis for conversions from RDF to Excel in part 2.

_**NOTE:** Having been run to generate SKOS RDF from the previous template, these scripts should NOT be run again and are retained for reference only_.


## 2. Vocabs to Excel

The script **make_excel_from_vocabs.py** creates an Excel workbook containing a single worksheet called VALIDATION_DICTIONARY that contains codelists from all the vocabularies in SKOS RDF in a given directory - the `vocabs-codelists` directory.

The script **make_excel_from_uom.py** similarly produces a single worksheet called UNITS_OF_MEASURE that contains collections of units of measure from the vocabulary in the `uom.ttl` within the `vocabs-uom` directory.

These script should be used to regenerate codelists and the units of measure collections whenever vocabularies are updated.

See the script itself for usage notes (top of the file).

New Concepts may be added to existing vocabularies and new vocabularies may be added to the directory and these will generate new codelists. For the UoM: new units can be added to the vocab but must be placed within one or more SKOS Collections in order to appear in one or more of the columns in the UNIS_OF_MEASURE worksheet.

New Concepts and vocabularies must follow the format of existing ones which is the same as all GSQ Concepts and vocabs however these used here must also contain a `skos:notation` property for each that supplies the code for the codelist, e.g., for the vocabulary Soil Colour:

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

For the unit of measure _Shots per foot_, it's Concept in the `uno.tt` vocab looks like this:

```
unit:SHOTS-PER-FT
    a skos:Concept ;
    skos:inScheme cs: ;
    rdfs:isDefinedBy units: ;
    skos:definition "Shots per foot" ;
    skos:notation "sht/ft" ;
    skos:prefLabel "Shots per foot" ;
    skos:topConceptOf cs: ;
.
```

Importantly, this unit is listed as being within the Units of Measure vocabulary's Concept Scheme (`cs: skos:hasTopConcept unit:SHOTS-PER-FT`) but it's also listed as being within the _Perf Spacigng_ SKOS Collection within the vocab too (`:perf-spacing skos:member unit:SHOTS-PER-FT`). It's this second listing that allows the Concept to be placed within the "Perf Spacing" column in the UNITS_OF_MEASURE workbook.


## 3. Validation using Vocabs

Data in Excel workbooks made using the v3 template must use codes given either in the VALIDATION_DICTIONARY, the UNITS_OF_MEASURE, the USER_DICTIONARY or the USER_UNITS_OF_MEASURE worksheets.

If codes are in the latter two, they are being defined by the data supplier and should be added to the vocabularies to appear in a later version of the VALIDATION_DICTIONARY and the UNITS_OF_MEASURE worksheets.

Validation of Excel data's values against vocabularies is done using the `geochemxl` module in the GSQ profile's `scripts/` directory which first converts a geochemistry Excel workbook to RDF data and then validates it, like this:

```
~$ ./geochemxl.sh {FILE_TO_CONVERT}
```

Any conversion errors or validation errors are output and, if there are none, then the RDF representation of the Excel data is output.

This conversion can also be done online at the [GSQL Geochemistry Data Portal](https://geochem.dev.kurrawong.ai/).

Behind-the-scenes, this conversion relies on a comparison of all the codes in the VALIDATION_DICTIONARY, the UNITS_OF_MEASURE to codes in vocabs to know that they are legitimate values and takes all the codes supplied in the  USER_DICTIONARY and the USER_UNITS_OF_MEASURE worksheets at face value.


## 4. Updating vocabs with Data Supplier's codes

When an Excel workbook is supplied that contains user-defined codes in either or both of the USER_DICTIONARY and the USER_UNITS_OF_MEASURE worksheets, the values from the worksheet will need to be entered into the relevant vocabularies by GSQ staff. To do this, the staff will need to read the USER_DICTIONARY or USER_UNITS_OF_MEASURE worksheet and manually enter the given codes into the appropriate vocabulary. Codes defined in the USER_DICTIONARY or USER_UNITS_OF_MEASURE worksheets are required to indicate the codelists they come from, so the relevant vocab should be easy to find. 

Once codes from a USER_DICTIONARY worksheet have been added to a vocab, the worksheet corresponding to that vocabulary - either VALIDATION_DICTIONARY or UNITS_OF_MEASURE - should be updated as per function _2. Vocabs to Excel_ above and a new version of the Excel template, v3.x, released