import simplegeo
from itertools import ifilter

client = simplegeo.context.Client('w9aKf7zBrxwW3L5YmRrb6yKqT7qAETYa','HT68BaFyJgcw5r8hrzedZXyzcg3desan')

location = client.get_context_by_address("41 Decatur St, San Francisco, CA")

# Find the bounding box of your current city
sf = next(ifilter(lambda feature: feature['classifiers'][0]['category'] == 'Administrative', location['features']), None)

hoods = client.get_features_from_bbox(sf['bounds'], features__category='Neighborhood')
for hood in hoods['features']:
...     print hood['properties']['name']
