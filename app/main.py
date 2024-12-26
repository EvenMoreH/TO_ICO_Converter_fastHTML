from fasthtml.common import * # type: ignore
# from fasthtml.common import (Form, Fieldset, Label, Input, Button, Html, Head, Body, Div, P, Title, Titled, A, Link, UploadFile)
from PIL import Image # type: ignore

app, rt = fast_app(static_path="static") # type: ignore


serve() # type: ignore