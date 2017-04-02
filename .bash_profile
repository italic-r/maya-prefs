# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# User specific environment and startup programs

# PYTHONPATH=/usr/lib64/python2.7/site-packages
PATH=$HOME/.local/bin:$HOME/bin:$PATH
C_INCLUDE_PATH=$HOME/include:$C_INCLUDE_PATH
CPLUS_INCLUDE_PATH=$HOME/include:$CPLUS_INCLUDE_PATH
LD_LIBRARY_PATH=$HOME/lib:$HOME/lib64:/usr/lib:/usr/lib64:$LD_LIBRARY_PATH

# Rust
source $HOME/.cargo/env

# Source variables

#export GIT_SSH=/usr/bin/ssh
PATH=$HOME/src/phab/arcanist/bin:$PATH
source $HOME/src/phab/arcanist/resources/shell/bash-completion

# Blender variables
export B3D_PY_PATH=/opt/lib/python-3.5
CUDA_PATH=/usr/local/cuda
PATH=$CUDA_PATH/bin:$HOME/blender:$PATH
C_INCLUDE_PATH=$CUDA_PATH/include:/opt/lib/openvdb/include:$B3D_PY_PATH/include:$C_INCLUDE_PATH
CPLUS_INCLUDE_PATH=$CUDA_PATH/include:/opt/lib/openvdb/include:$B3D_PY_PATH/include:$CPLUS_INCLUDE_PATH
LD_LIBRARY_PATH=$CUDA_PATH/lib64:$B3D_PY_PATH/lib:/opt/lib/python-3.5-bpy/lib:$LD_LIBRARY_PATH
CYCLES_CUDA_ADAPTIVE_COMPILE=1

# Maya variables
MAYA_APP_DIR=$HOME/maya
MAYA_MODULE_PATH=$HOME/maya/modules
RMANTREE=/opt/pixar/RenderManProServer-20.9
RMSTREE=/opt/pixar/RenderManStudio-20.9-maya2016
PATH=$RMSTREE/bin:$HOME/bin:opt/pixar/RenderManProServer-20.9/bin:$PATH


# export PYTHONPATH
export PATH
export C_INCLUDE_PATH
export CPLUS_INCLUDE_PATH
export LD_LIBRARY_PATH

export MAYA_APP_DIR
export MAYA_MODULE_DIR
export RMANTREE
export RMSTREE
