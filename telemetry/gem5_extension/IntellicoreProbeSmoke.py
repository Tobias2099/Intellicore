from m5.objects.BaseMemProbe import BaseMemProbe


class IntellicoreProbeSmoke(BaseMemProbe):
    type = "IntellicoreProbeSmoke"
    cxx_header = "intellicore_probe_smoke.hh"
    cxx_class = "gem5::IntellicoreProbeSmoke"
