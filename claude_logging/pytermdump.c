#define PY_SSIZE_T_CLEAN
#include <Python.h>

// No need to define TERMDUMP_LIB anymore since it's the default behavior
#include "termdump.c"

static PyObject* pytermdump_termdump(PyObject *self, PyObject *args) {
    Py_buffer buffer;
    PyObject *result = NULL;
    char *processed_data;
    size_t processed_len;

    /* Parse the bytes/buffer object */
    if (!PyArg_ParseTuple(args, "y*", &buffer)) {
        return NULL;
    }

    /* Process the buffer */
    processed_data = process_buffer((const unsigned char*)buffer.buf, buffer.len, &processed_len);
    if (!processed_data) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory for result");
        PyBuffer_Release(&buffer);
        return NULL;
    }

    /* Create a new bytes object with the processed data */
    result = PyBytes_FromStringAndSize(processed_data, processed_len);
    
    /* Clean up */
    free(processed_data);
    PyBuffer_Release(&buffer);
    
    return result;
}

/* Module method definitions */
static PyMethodDef PytermdumpMethods[] = {
    {"termdump", pytermdump_termdump, METH_VARARGS, "Process terminal escape sequences in a buffer."},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

/* Module definition */
static struct PyModuleDef pytermdumpmodule = {
    PyModuleDef_HEAD_INIT,
    "claude_logging.pytermdump",     /* name of module */
    "Python wrapper for termdump utility", /* module documentation */
    -1,               /* size of per-interpreter state (-1 = in global vars) */
    PytermdumpMethods
};

/* Module initialization function */
PyMODINIT_FUNC PyInit_pytermdump(void) {
    return PyModule_Create(&pytermdumpmodule);
}