from groupmne import (compute_fwd, get_src_reference, compute_gains,
                      compute_inv_data, compute_group_inverse)
import mne
from mne.datasets import testing
import numpy as np
import os.path as op
import os


data_path = testing.data_path(download=True)
subjects_dir = op.join(data_path, 'subjects')

bem_fname = op.join(data_path, 'subjects', 'sample', 'bem',
                    'sample-1280-1280-1280-bem-sol.fif')
fname_fs = op.join(subjects_dir, 'fsaverage', 'bem', 'fsaverage-ico-5-src.fif')
trans_fname = op.join(data_path, 'MEG', 'sample',
                      'sample_audvis_trunc-trans.fif')

raw_fname = op.join(data_path, 'MEG', 'sample',
                    'sample_audvis_trunc_raw.fif')
ave_fname = op.join(data_path, 'MEG', 'sample',
                    'sample_audvis_trunc-ave.fif')
cov_fname = op.join(data_path, 'MEG', 'sample',
                    'sample_audvis_trunc-cov.fif')
rng = np.random.RandomState(0)
resolution = 3
spacing = "ico%d" % resolution
os.environ['SUBJECTS_DIR'] = subjects_dir


@testing.requires_testing_data
def test_gains():
    src_ref = get_src_reference(spacing=spacing, subjects_dir=subjects_dir)
    fwd0 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=5)
    fwd1 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=10)
    fwds = [fwd0, fwd1]
    gains, group_info = compute_gains(fwds, src_ref, ch_type="grad",
                                      hemi="lh")
    n_ch = len(group_info["sel"])
    n_s = group_info["n_sources"][0]
    assert gains.shape == (2, n_ch, n_s)


@testing.requires_testing_data
def test_inverse_data():
    src_ref = get_src_reference(spacing=spacing, subjects_dir=subjects_dir)
    fwd0 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=5)
    fwd1 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=10)
    fwds = [fwd0, fwd1]
    ev = mne.read_evokeds(ave_fname)[0]
    cov = mne.read_cov(cov_fname)
    evoked_s = [ev, ev]
    covs = [cov, cov]
    gains, M, group_info = \
        compute_inv_data(fwds, src_ref, evoked_s, covs,
                         ch_type="grad", tmin=0.02, tmax=0.04)
    n_ch = len(group_info["sel"])
    n_s = sum(group_info["n_sources"])
    n_t = ev.crop(0.02, 0.04).times.shape[0]
    assert gains.shape == (2, n_ch, n_s)
    assert M.shape == (2, n_ch, n_t)


@testing.requires_testing_data
def test_inverse():
    src_ref = get_src_reference(spacing=spacing, subjects_dir=subjects_dir)
    fwd0 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=5)
    fwd1 = compute_fwd("sample", src_ref, raw_fname, trans_fname, bem_fname,
                       mindist=10)
    fwds = [fwd0, fwd1]
    ev = mne.read_evokeds(ave_fname)[0]
    cov = mne.read_cov(cov_fname)
    evoked_s = [ev, ev]
    covs = [cov, cov]
    gains, M, group_info = \
        compute_inv_data(fwds, src_ref, evoked_s, covs,
                         ch_type="grad", tmin=0.02, tmax=0.04)

    stcs, log = compute_group_inverse(gains, M, group_info,
                                      method="grouplasso", depth=0.9,
                                      alpha=0.1, return_stc=True,
                                      n_jobs=-1)
    assert len(stcs) == len(fwds)
    n_s = gains.shape[-1]
    n_t = M.shape[-1]
    assert stcs[0].data.shape == (n_s, n_t)
