import wrappers.qiskit_wrapper as qiskit_wrapper

from qEmQUIP import QEM, conf

CB_color_cycle = ['#1F77B4', '#AEC7E8', '#FF7F0E', '#FFBB78', '#2CA02C', '#98DF8A', '#D62728', '#FF9896',
                  '#9467BD', '#C5B0D5', '#8C564B', '#C49C94', '#E377C2', '#F7B6D2', '#7F7F7F', '#C7C7C7',
                  '#BCBD22', '#DBDB8D', '#17BECF', '#9EDAE5'
                  ]

markers = ['o', 'v', '^', 's', '+', '*', 'x', 'd', '<', '>', 'p']
linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':']
token = "476ea8c61cc54f36e4a21d70a8442f94203c9d87096eaad0886a3e8154d8c2e79bcad6f927c6050a76335dd68d783f478c1b828504748a4377b441c335c831aa"

# select compilation techniques
compilations = ["qiskit_3", "triq_avg_sabre", "triq_lcd_sabre"]

# Setup the object for n3_x
q = QEM(runs=conf.runs, user_id=conf.user_id, token=token)

# update TriQ configs from calibration data
q.update_hardware_configs()

# update IBM FakeBackend configuration
shots = 1000
q.set_backend(program_type="sampler", shots=shots)
qiskit_wrapper.generate_new_props(q.backend, "avg")
qiskit_wrapper.generate_new_props(q.backend, "mix")
qiskit_wrapper.generate_new_props(q.backend, "recent_15_adjust")