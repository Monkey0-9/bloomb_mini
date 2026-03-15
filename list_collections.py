import pystac_client
client = pystac_client.Client.open("https://catalogue.dataspace.copernicus.eu/stac")
for collection in client.get_collections():
    print(collection.id)
