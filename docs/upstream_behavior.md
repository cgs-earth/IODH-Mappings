It appears that pages are limited to 100 when requesting locations but unbounded when requesting results

```
curl  "https://data.usbr.gov/rise/api/location?include=catalogRecords.catalogItems&page=1&itemsPerPage=5000" | jq '.data | length'
```


It appears that the same  

```
pages = await self.get_or_fetch_group(urls, force_fetch=force_fetch)
found = {}
for base_url in pages:
    for location in pages[base_url]["data"]:
        id = location["attributes"]["_id"]

        if id in found:
            data = found[id]
            raise RuntimeError(
                f"{id} previously had {data} but now has {base_url}"
            )

        found[id] = {
            "url": base_url,
            "data": location["attributes"]["_id"],
        }
                ```