# docker build -t cresi_v3_image_cpu .
# nvidia-docker run -it --ipc=host -v /local_data:/local_data/ -p 9111:9111 --name cresi_v3 cresi_v3_image
# To use jupyter notebook, inside container run:
# jupyter notebook --ip 0.0.0.0 --no-browser --allow-root --port=9111
# back on local machine, invoke the following in a web browser: https://localhost:9111
FROM ubuntu:22.04
###############################################
# Install necessary dependencies
#	RUN apt-get update && apt-get install -y \
#		wget \
#		bzip2 \
#		ca-certificates \
#		curl \
#		git \
#		&& rm -rf /var/lib/apt/lists/*
## Download and install Miniforge
#	RUN wget --quiet https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && \
#		/bin/bash ~/miniforge.sh -b -p /opt/conda && \
#		rm ~/miniforge.sh

# Update Conda and add conda-forge channel
#	RUN /opt/conda/bin/conda update -n base -c defaults conda && \
#		/opt/conda/bin/conda config --add channels conda-forge

# Ensure conda is available in PATH
#	ENV PATH /opt/conda/bin:$PATH
###############################################
# prep apt-get and cudnn
RUN apt-get update && apt-get install -y --no-install-recommends \
	    apt-utils && \
    rm -rf /var/lib/apt/lists/*

# install requirements
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
	apt-utils \
	bc \
	bzip2 \
	ca-certificates \
	curl \
	git \
	libgdal-dev \
	libssl-dev \
	libffi-dev \
	libncurses-dev \
	libgl1 \
	jq \
	nfs-common \
	parallel \
	python3-dev \
	python3-pip \
	python3-wheel \
	python3-setuptools \
	unzip \
	vim \
	tmux \
	wget \
	build-essential \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]
ENV PATH /opt/conda/bin:$PATH
LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format72
# install anaconda 
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
	/opt/conda/bin/conda clean -a && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

ENV TINI_VERSION v0.16.1
LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format83ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

# Install ca-certificates
RUN apt-get update && apt-get install -y ca-certificates

# Use conda-forge instead of default channel
RUN conda config --set ssl_verify true && \
    conda update conda && \
    conda config --add channels conda-forge

# Set up conda environment and add to $PATH
RUN conda create -n cresi python=3.6 \
    && echo "source activate cresi" > ~/.bashrc
ENV PATH /opt/conda/envs/cresi/bin:$PATH
legacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format98
# use conda-forge instead of default channel
#RUN conda update conda && \
#    conda config --add channels 'conda-forge'

# set up conda environment and add to $PATH
#RUN conda create -n cresi python3=3.6 \
#                    && echo "source activate cresi" > ~/.bashrc
#ENV PATH /opt/conda/envs/cresi/bin:$PATH



#RUN mkdir -p /root/.torch/models
#RUN wget --no-check-certificate https://download.pytorch.org/models/resnet34-333f7ec4.pth -P /root/.torch/models
#RUN pip install http://download.pytorch.org/whl/cpu/torch-0.4.1-cp36-cp36m-linux_x86_64.whl
#RUN pip install torchvision
#RUN pip install tensorboardX
#RUN pip install utm
#RUN pip install numba
#RUN pip install torchsummary
#RUN pip install imagecodecs



# get pytorch
# https://pytorch.org/get-started/previous-versions/
RUN mkdir -p /root/.torch/models
RUN wget --no-check-certificate https://download.pytorch.org/models/resnet34-333f7ec4.pth -P /root/.torch/models
RUN pip install --no-cache-dir --trusted-host download.pytorch.org \
    http://download.pytorch.org/whl/cpu/torch-0.4.1-cp36-cp36m-linux_x86_64.whl && \
    pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    torchvision tensorboardX utm numba torchsummary imagecodecs
#RUN pip install --trusted-host https://download.pytorch.org/whl/cpu/torch-0.4.1-cp36-cp36m-linux_x86_64.whl \
#RUN pip install http://download.pytorch.org/whl/cpu/torch-0.3.0.post4-cp36-cp36m-linux_x86_64.whl \
&& pip install torchvision \
&& pip install tensorboardX \
#&& pip install utm \
#&& pip install numba \
#&& pip install torchsummary \
#&& pip install imagecodecs
			  
RUN conda install -n cresi \
		gdal=2.4.2 \
		geopandas=0.6.3 \
		fiona \
		rasterio \
		osmnx=0.12 \
		networkx=2.2 \ 
		awscli \
		affine \
		pyproj \
		pyhamcrest \
		cython \
		fiona \
		h5py \
		ncurses \
		jupyter \
		jupyterlab \
		ipykernel \
		libgdal \
		matplotlib \
		ncurses \
		numpy \
		statsmodels \
		#opencv \
		pandas \
		pillow \
		pip \
		scipy \
		scikit-image \
		scikit-learn \
		shapely \
		rtree \
		testpath \
		tqdm \
		pandas \
		opencv \
		jupyter \
		jupyterlab \
		ipykernel \
	&& conda clean -p \
	&& conda clean -t \
	&& conda clean --yes --all
	
	
ENV LD_LIBRARY_PATH /miniconda/lib:${LD_LIBRARY_PATH}
UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH'184#RUN apt install -y libgl1-mesa-glx
RUN apt install -y libgl1
					 
# add a jupyter kernel for the conda environment in case it's wanted
RUN source activate cresi && python3 -m ipykernel.kernelspec

# # clone cresi
	#Certificates
	#@COPY server-ca.crt /usr/local/share/ca-certificates/
	#RUN update-ca-certificates
#RUN apt-get update && apt-get install -y ca-certificates
RUN git config --global http.sslVerify false
RUN git clone https://github.com/avanetten/cresi.git /opt/cresi/

# TensorBoard
EXPOSE 6006
# Ipython3
EXPOSE 9111

WORKDIR "/opt/cresi"
RUN ["/bin/bash"]
