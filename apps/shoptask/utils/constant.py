from django.utils.translation import ugettext_lazy as _

# GLOBAL
DRAFT = 'draft'
PUBLISH = 'publish'

# PURCHASE STATUS
SUBMITTED = 'submitted'
REVIEWED = 'reviewed'
ACCEPT = 'accept'
ASSIGNED = 'assigned'
PROCESSED = 'processed'
REJECTED = 'rejected'
DONE = 'done'
STATUS_CHOICES = (
    (DRAFT, _("Draft")),
    (SUBMITTED, _("Submitted")),
    (REVIEWED, _("Reviewed")),
    (ACCEPT, _("Accept")),
    (ASSIGNED, _("Assigned")),
    (PROCESSED, _("Processed")),
    (REJECTED, _("Rejected")),
    (DONE, _("Done")),
)
ALLOWED_DELETE_STATUS = [REJECTED, DRAFT]


# Metrics
KILOGRAM = 'kg'
HECTOGRAM = 'hg'  # similar to ONS
GRAM = 'g'
MILLIGRAM = 'mg'
LITER = 'liter'
PACK = 'pack'
POUCH = 'pouch'
PIECE = 'piece'
BUNCH = 'bunch'
SACK = 'sack'
UNIT = 'unit'
METRICS = (
    (KILOGRAM, _("Kilogram")),
    (HECTOGRAM, _("Ons")),
    (GRAM, _("Gram")),
    (MILLIGRAM, _("Miligram")),
    (LITER, _("Liter")),
    (PACK, _("Bungkus")),
    (POUCH, _("Kantung")),
    (PIECE, _("Buah")),
    (BUNCH, _("Ikat")),
    (SACK, _("Karung / Sak")),
    (UNIT, _("Unit")),
)


# Catalog
CATALOG_STATUS = (
    (DRAFT, _("Draft")),
    (PUBLISH, _("Publish")),
)


# Weight
WEIGHT_METRICS = (
    (KILOGRAM, _("Kilogram")),
    (HECTOGRAM, _("Ons")),
    (GRAM, _("Gram")),
    (MILLIGRAM, _("Miligram")),
)


# Dimension
KILOMETRE = 'km'
METRE = 'm'
CENTIMETRE = 'cm'
MILLIMETRE = 'mm'
DIMENSION_METRICS = (
    (KILOMETRE, _("Kilometer")),
    (METRE, _("Meter")),
    (CENTIMETRE, _("Sentimeter")),
    (MILLIMETRE, _("Milimeter")),
)


WEIGHT = 'weight'
WIDTH = 'width'
DEPTH = 'depth'
HEIGHT = 'height'
CATALOG_ATTRIBUTES = (
    (WEIGHT, _("Berat")),
    (WIDTH, _("Panjang")),
    (DEPTH, _("Lebar")),
    (HEIGHT, _("Tinggi")),
)
CATALOG_ATTRIBUTE_METRICS = METRICS + DIMENSION_METRICS
