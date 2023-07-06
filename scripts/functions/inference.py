import arviz as az
import jax.numpy as jnp

################################################################################
################################################################################
##############################   MAIN FUNCTIONS   ##############################
################################################################################
################################################################################

def calc_mean_hpdi(arviz_post, ci=0.89, y_scaler=None):
    # get the mean and hpdi of mu/sim
    mean_mu = arviz_post.posterior['y_out'].mean(dim=['chain','draw']).values
    # hpdi is used to compute the credible intervals corresponding to ci
    hpdi_mu = az.hdi(
        arviz_post.posterior, hdi_prob=ci, var_names=['y_out']
    ).transpose('hdi','y_out_dim_0','y_out_dim_1')['y_out'].values
    hpdi_sim = az.hdi(
        arviz_post.posterior_predictive, hdi_prob=ci, var_names=['obs']
    ).transpose('hdi','obs_dim_0','obs_dim_1')['obs'].values

    if not y_scaler is None:
        # unscale before exp
        mean_mu = y_scaler.inverse_transform(mean_mu)
        hpdi_mu[0,...] = y_scaler.inverse_transform(hpdi_mu[0,...])
        hpdi_mu[1,...] = y_scaler.inverse_transform(hpdi_mu[1,...])
        hpdi_sim[0,...] = y_scaler.inverse_transform(hpdi_sim[0,...])
        hpdi_sim[1,...] = y_scaler.inverse_transform(hpdi_sim[1,...])
        # reverse the log transform
        mean_mu = jnp.exp(mean_mu)
        hpdi_mu = jnp.exp(hpdi_mu)
        hpdi_sim = jnp.exp(hpdi_sim)
    return mean_mu, hpdi_mu, hpdi_sim
        
################################################################################
################################################################################
