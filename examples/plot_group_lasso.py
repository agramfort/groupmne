"""
Multi-subject joint source localization with multi-task models
==============================================================

The aim of this tutorial is to show how to leverage functional similarity
across subjects to improve source localization. For that purpose we use the
the high frequency SEF MEG dataset of (Nurminen et al., 2017) which provides
MEG and MRI data for two subjects.
"""

# Author: Hicham Janati (hicham.janati@inria.fr)
#
# License: BSD (3-clause)

import os
import os.path as op
from mne import compute_covariance, pick_types
from mne.parallel import parallel_func
from mne.datasets import hf_sef
from matplotlib import pyplot as plt

from groupmne import group_model
from groupmne.inverse import compute_group_inverse

##########################################################
# Download and process MEG data
# -----------------------------
#
# We need the raw data to estimate the noise covariance
# since only average MEG data (and MRI) are provided in "evoked".
# The data will be downloaded in the same location

# _ = hf_sef.data_path("raw")
# data_path = hf_sef.data_path("evoked")
# meg_path = data_path + "/MEG/"
#
# data_path = op.expanduser(data_path)
# subjects_dir = data_path + "/subjects/"
# os.environ['SUBJECTS_DIR'] = subjects_dir
#
# raw_name_s = [meg_path + s for s in ["subject_a/sef_right_raw.fif",
#               "subject_b/hf_sef_15min_raw.fif"]]

#
# def process_meg(raw_name):
#     from mne.io import read_raw_fif
#     from mne import find_events, Epochs
#     raw = read_raw_fif(raw_name)
#     events = find_events(raw)
#     # we keep only
#     events = events[:300]
#     event_id = dict(hf=1)  # event trigger and conditions
#     tmin = -0.05  # start of each epoch (50ms before the trigger)
#     tmax = 0.3  # end of each epoch (300ms after the trigger)
#     baseline = (None, 0)  # means from the first instant to t = 0
#     epochs = Epochs(raw, events, event_id, tmin, tmax, proj=True,
#                     baseline=baseline)
#     del raw, events
#     return epochs
#
#
# evoked_s = []
#
# # compute noise covariance (takes a few minutes)
# noise_cov_s = []
# for subj, raw_name in zip(["a", "b"], raw_name_s):
#     ep = process_meg(raw_name)
#     ev = ep.average()
#     evoked_s.append(ev)
#     cov = compute_covariance(ep, tmin=None, tmax=0.)
#     del ep, ev
#     noise_cov_s.append(cov)
#
# f, axes = plt.subplots(1, 2, sharey=True)
# for ax, ev, nc, ll in zip(axes.ravel(), evoked_s, noise_cov_s, ["a", "b"]):
#     picks = pick_types(ev.info, meg="grad")
#     ev.plot(picks=picks, axes=ax, noise_cov=nc, show=False)
#     ax.set_title("Subject %s" % ll, fontsize=15)
# plt.show()
#
# #########################################################
# # Source and forward modeling
# # ---------------------------
# # To guarantee an alignment across subjects, we start by
# # computing (or reading if available) the source space of the average
# # subject of freesurfer `fsaverage`
# # If fsaverage is not available, it will be fetched to the data_path
#
# resolution = 4
# spacing = "ico%d" % resolution
# src_ref = group_model.get_src_reference(spacing=spacing,
#                                         subjects_dir=subjects_dir)
#
# ###################################################################
#
# # the function group_model.compute_fwd morphs the source space src_ref to
# # the surface of each subject by mapping the sulci and gyri patterns
# # and computes their forward operators
#
# subjects = ["subject_a", "subject_b"]
# trans_fname_s = [meg_path + "%s/sef-trans.fif" % s for s in subjects]
# bem_fname_s = [subjects_dir + "%s/bem/%s-5120-bem-sol.fif" % (s, s)
#                for s in subjects]
# n_jobs = 2
# parallel, run_func, _ = parallel_func(group_model.compute_fwd,
#                                       n_jobs=n_jobs)
#
# fwds = parallel(run_func(s, src_ref, info, trans, bem,  mindist=3)
#                 for s, info, trans, bem in zip(subjects, raw_name_s,
#                                                trans_fname_s, bem_fname_s))
#
# ############################################
# # We can now compute the data of the inverse problem.
# # `group_info` is a dictionary that contains the selected channels and the
# # alignment maps between src_ref and the subjects which are required if you
# # want to plot source estimates on the brain surface of each subject.
#
# gains, M, group_info = \
#     group_model.compute_inv_data(fwds, src_ref, evoked_s, noise_cov_s,
#                                  ch_type="grad", tmin=0.02, tmax=0.04)
# print("(# subjects, # channels, # sources) = ", gains.shape)
# print("(# subjects, # channels, # time points) = ", M.shape)
#
# ############################################
# # Solve the inverse problems
# # --------------------------
# #
# stcs, log = compute_group_inverse(gains, M, group_info,
#                                   method="grouplasso",
#                                   depth=0.9, alpha=0.1, return_stc=True,
#                                   n_jobs=4)
# t = 0.025
# t_idx = stcs[0].time_as_index(t)
# for stc, subject in zip(stcs, subjects):
#     m = abs(stc.data[:group_info["n_sources"][0], t_idx]).max()
#     surfer_kwargs = dict(
#         clim=dict(kind='value', pos_lims=[0., 0.1 * m, m]),
#         hemi='lh', subjects_dir=subjects_dir, views='lateral',
#         initial_time=t, time_unit='s', size=(800, 800),
#         smoothing_steps=5)
#     brain = stc.plot(**surfer_kwargs)
#     brain.add_text(0.1, 0.9, subject, "title")
