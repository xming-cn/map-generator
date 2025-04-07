#!/bin/bash
pkill streamlit
nohup streamlit run website.py --server.port 80  > std.out 2>&1 &