source .venv/bin/activate

if [[ "${PYTHONPATH_SAVED}" != "" ]]; then
  export PYTHONPATH=${PYTHONPATH_SAVED}
  export PYTHONPATH_SAVED=
fi

deactivate

