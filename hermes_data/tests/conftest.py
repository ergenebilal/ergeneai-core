import warnings

# Python 3.11'de httplib2 -> pyparsing -> sre_constants deprecation
# uyarisi tum testleri -W error modunda kiriyor. Sadece bunu sessize al.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*sre_constants.*",
)
