library(tidyverse)
# the json and rdf files were exported from Zotero

ipa <- jsonlite::fromJSON(normalizePath("~/Downloads/ipa_nov_2023.json"), 
                          simplifyVector = FALSE,
                          simplifyDataFrame = TRUE)
ipa <- mutate(ipa,
              issuedate = map_chr(issued[[1]], ~paste(.x, collapse="-")),
              issuedate = lubridate::parse_date_time(issuedate, c("ym", "ymd")))

ipa <- mutate(ipa, 
              ISOpresent = str_detect(abstract, "IS[O0]"))
ipa <- arrange(ipa, issuedate)

ipa <- mutate(ipa, 
              author_family = map_chr(author, ~paste0(.x$family, collapse=";")),
              author_given = map_chr(author, ~paste0(.x$given, collapse=";"))
              )

# No volume or issue before print version
ipa_save <- select(ipa, title, author, author_family, author_given, DOI, page,	URL, issuedate)

# title	author	year	doi	volume	issue	pages	DA	ISOcodeEdited	SoundFiles	url
ipa_save <- rename(ipa_save, doi=DOI, pages=page, url=URL)
ipa_save <- mutate(ipa_save, ISOcodeEdited=NA, volume=NA, issue=NA, SoundFiles=NA, DA=format(ipa$issuedate, "%Y/%m/%d"), year=lubridate::year(issuedate))
ipa_save <- select(ipa_save, title, author, author_family, author_given, year, doi, volume, issue, pages, DA, ISOcodeEdited, SoundFiles, url)
openxlsx::write.xlsx(ipa_save, "new_202311.xlsx")
