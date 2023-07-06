import os
import pandas as pd
import numpy as np
import seaborn as sns
import contextily as ctx
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import plotly.graph_objects as go
from plotly.subplots import make_subplots

################################################################################
################################################################################
##############################   MAIN FUNCTIONS   ##############################
################################################################################
################################################################################

def plot_probe_locations(loc_meta,plot_col='treatment rep',plot_title=None,save_loc=None):
    sns.set_style('ticks')
    sns.set_context('poster')

    if plot_title is None:
        # space saver
        plot_title = 'Soil Moisture Probe Locations'

    # Calculate the mean longitude and latitude values (to the 100)
    mean_x = np.round(loc_meta.geometry.centroid.x.mean()/100,0)*100
    mean_y = np.round(loc_meta.geometry.centroid.y.mean()/100,0)*100

    # Subtract the mean values from each point
    plot_meta = loc_meta.copy()
    # plot_meta.geometry = loc_meta.geometry.translate(-mean_x, -mean_y)

    label_lookup = {
        'variance': r'$\sigma$',
        'beta_r0': r'$\beta_{r0}$',
        'beta_r1': r'$\beta_{r1}$',
        'beta_trend': r'$\beta_{trend}$',
        'beta_ar1': r'$\beta_{AR1}$'
    }

    # Plot the location metadata, coloring by the 'treatment rep' column
    # ax = loc_meta.plot(column=plot_col, legend=True,cmap='bwr_r',figsize=(6.5,2))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18,6), gridspec_kw={'width_ratios': [0.925, 2]})
    vmin = plot_meta[plot_col].min()
    vmax = plot_meta[plot_col].max()
    ms = 400
    plot_meta.query('site=="WW"').plot(
        column=plot_col, vmin=vmin, vmax=vmax,
        legend=False,cmap='bwr_r',ax=ax1,
        markersize=ms, edgecolor='xkcd:dark grey',linewidth=2
    )
    plot_meta.query('site=="WE"').plot(
        column=plot_col, vmin=vmin, vmax=vmax,
        legend=True,cmap='bwr_r',ax=ax2,
        legend_kwds={'label': label_lookup[plot_col], 'fmt': '{:.2f}'},
        markersize=ms, edgecolor='xkcd:dark grey',linewidth=2
    )

    # Add the satellite background image
    ctx.add_basemap(ax1, crs=plot_meta.crs.to_string(), source=ctx.providers.Esri.WorldImagery)
    ctx.add_basemap(ax2, crs=plot_meta.crs.to_string(), source=ctx.providers.Esri.WorldImagery)

    # We will add this into the figure caption for aesthetics
    #'Tiles (C) Esri -- Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community')'
    ax1.texts[0].remove()
    ax2.texts[0].remove()

    # Set the axis tick labels - removing the mean so we don't have ridiculous numbers
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda val, _: remove_mean(val, mean_x)))
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda val, _: remove_mean(val, mean_y)))
    ax2.xaxis.set_major_formatter(FuncFormatter(lambda val, _: remove_mean(val, mean_x)))
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda val, _: remove_mean(val, mean_y)))

    # Set the axis labels/title
    fig.suptitle(plot_title)
    ax1.set_title('WW',pad=10)
    ax2.set_title('WE',pad=10)
    ax1.set_xlabel('Eastings (relative)',labelpad=10)
    ax2.set_xlabel('Eastings (relative)',labelpad=10)
    ax1.set_ylabel('Northings (relative)',labelpad=10)
    if not save_loc is None:
        os.makedirs(save_loc,exist_ok=True)
        fig.savefig(
            os.path.join(save_loc,'spatial_{}.png'.format(plot_col)),
            dpi=300,bbox_inches='tight'
        )
    plt.show()


################################################################################
################################################################################

# Define the formatter function
def remove_mean(val, mean_val):
    return '{:.0f}'.format(val - mean_val)

################################################################################
################################################################################

# function to plot R2 of soil moisture to rainfall and various lag in rainfall
def plot_r2_lag(rain_data,sm_data,rain_name,sm_name,lag):
    # get the data
    rain = rain_data[rain_name]
    sm = sm_data
    # combine the two dataframes
    df = pd.concat([rain,sm],axis=1)
    # now plot with plotly express top plot should be a barplot of rainfall in the y and index in the x,
    # bottom plot should be the timeseries of soil moisture
    fig = make_subplots(rows=2,cols=1,shared_xaxes=True)
    fig.add_trace(go.Bar(x=df.index,y=df[rain_name],name=rain_name),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df[sm_name],name=sm_name),row=2,col=1)
    fig.update_layout(height=400,width=600)
    fig.show()

    sm = sm.diff()
    sm.columns = [_ + '_diff' for _ in sm.columns]
    
    #.diff()
    # shift the rain data by the lag
    rain_shift = rain.shift(lag)
    lag_plot = pd.concat([rain_shift,sm, sm_data],axis=1)
    lag_plot.dropna(inplace=True)
    lag_plot['no_rain'] = lag_plot[rain_name]>0
    lag_plot['recession'] = lag_plot[sm_name]<0
    # plot
    fig_mpl, ax = plt.subplots(figsize=(4,3))
    sns.scatterplot(data=lag_plot,x=rain_name,y=sm_name+'_diff',hue=sm_name,s=30,alpha=0.75,palette='viridis',ax=ax)
    ax.set_title('R2 = {:.2f}'.format(lag_plot.corr().iloc[0,1]**2))
    ax.set_xlabel(f'{rain_name} shifted by {lag} days')
    ax.set_ylabel(f'{sm_name} - v2')
    plt.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    plt.show()
    return

################################################################################
################################################################################

def plot_site_prediction(df_Y, site_ii, mean_mu, hpdi_mu, hpdi_sim,ci=0.89,save_loc=None):
    sns.set_style('ticks')
    sns.set_context('paper')

    # Get the name of the site being plotted
    site_name = df_Y.columns[site_ii]
    # Create a new figure with the specified size
    fig = plt.figure(figsize=(7,3))
    # Create a new subplot for the plot
    ax1 = plt.subplot(111)
    # Plot the modelled soil moisture values
    ax1.plot(df_Y.index,mean_mu[:,site_ii],label='Modelled')
    # Shade the area between the upper and lower bounds of the simulated confidence interval
    ax1.fill_between(df_Y.index,hpdi_sim[0,:,site_ii],hpdi_sim[1,:,site_ii],alpha=0.25,color='C1',label='Simulated {:.0f}% CI'.format(ci*100))
    # Shade the area between the upper and lower bounds of the modelled confidence interval
    ax1.fill_between(df_Y.index,hpdi_mu[0,:,site_ii],hpdi_mu[1,:,site_ii],alpha=0.5,color='C0',label='Modelled {:.0f}% CI'.format(ci*100))
    # Plot the observed soil moisture values
    ax1.plot(df_Y.index,df_Y.iloc[:,site_ii],label='Observed')
    # Set the title, x-axis label, and y-axis label for the plot
    ax1.set_title(site_name)
    ax1.set_ylabel('Soil Moisture')
    ax1.set_xlabel('Date')
    # Rotate and align the tick labels on the x-axis so they look better
    fig.autofmt_xdate()
    # Add a legend to the plot
    lgd = plt.legend(loc='center left', bbox_to_anchor=(1.01, 0.5))
    if not save_loc is None:
        os.makedirs(save_loc,exist_ok=True)
        fig.savefig(
            os.path.join(save_loc,'modelled_site_{}.png'.format(site_name)),
            dpi=300,bbox_inches='tight',bbox_extra_artists=(lgd,)
        )
        plt.close()
    else:      
        # Display the plot
        plt.show()

################################################################################
################################################################################

def adjust_forest_labels(ax):
    # get the y tick labels
    yticklabels = ax.get_yticklabels()

    # loop through the labels and modify them to title case
    for label in yticklabels:
        text = label.get_text()
        title_text = text.replace('alpha_r0_mu',r'$\alpha_{r0')
        title_text = title_text.replace('alpha_r1_mu',r'$\alpha_{r1')
        title_text = title_text.replace('alpha_trend_mu',r'$\alpha_{trend')
        title_text = title_text.replace('alpha_ar1_mu',r'$\alpha_{AR1')
        title_text = title_text.replace(']',r']}$')
        if not 'alpha' in text:
            title_text = title_text.replace('[',r'$_{[')
        label.set_text(title_text)
        
    # update the axis object with the modified labels
    ax.set_yticklabels(yticklabels)
    return ax


################################################################################
################################################################################
