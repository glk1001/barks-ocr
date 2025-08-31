source .venv/bin/activate

if [[ "${PYTHONPATH_SAVED}" == "" ]]; then
  export PYTHONPATH_SAVED=${PYTHONPATH}
fi

export PYTHONPATH=$PWD

