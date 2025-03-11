It appears that pages are limited to 100 when requesting locations but unbounded when requesting results

```
curl  "https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems&page=1&itemsPerPage=5000" | jq '.data | length'
```