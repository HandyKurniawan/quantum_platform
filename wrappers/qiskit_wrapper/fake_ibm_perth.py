import os
from qiskit.providers.fake_provider import GenericBackendV2

class NewFakePerth(GenericBackendV2):
    """A fake 7 qubit backend."""
    dirname = os.path.expanduser("./wrappers/qiskit_wrapper/fake_backend/ibm_perth")

    conf_filename = "conf_perth.json"
    defs_filename = "defs_perth.json"

    props_filename = "props_ibm_perth.json"
    backend_name = "new_fake_ibm_perth"

class NewFakePerthRealAdjust(NewFakePerth):
    props_filename = "props_ibm_perth_real_adjust.json"
    backend_name = "new_fake_ibm_perth_real_adjust"

class NewFakePerthRecent15(NewFakePerth):
    props_filename = "props_ibm_perth_recent_15.json"
    backend_name = "new_fake_ibm_perth_recent_15"

class NewFakePerthRecent15Adjust(NewFakePerth):
    props_filename = "props_ibm_perth_recent_15_adjust.json"
    backend_name = "new_fake_ibm_perth_recent_15_adjust"

class NewFakePerthMix(NewFakePerth):
    props_filename = "props_ibm_perth_mix.json"
    backend_name = "new_fake_ibm_perth_mix"

class NewFakePerthMixAdjust(NewFakePerth):
    props_filename = "props_ibm_perth_mix_adjust.json"
    backend_name = "new_fake_ibm_perth_mix_adjust"

class NewFakePerthAverage(NewFakePerth):
    props_filename = "props_ibm_perth_avg.json"
    backend_name = "new_fake_ibm_perth_avg"

class NewFakePerthAverageAdjust(NewFakePerth):
    props_filename = "props_ibm_perth_avg_adjust.json"
    backend_name = "new_fake_ibm_perth_avg_adjust"

