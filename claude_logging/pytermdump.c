#define PY_SSIZE_T_CLEAN
// Make sure this is defined BEFORE including Python.h
#define Py_LIMITED_API 0x03080000  // Target Python 3.8 limited API
#include <Python.h>

// Verify we're using limited API
#ifndef Py_LIMITED_API
#error "Py_LIMITED_API not defined after inclusion of Python.h"
#endif

// No need to define TERMDUMP_LIB anymore since it's the default behavior
#include "termdump.c"

static PyObject* pytermdump_termdump(PyObject *self, PyObject *args) {
    PyObject *bytes_obj;
    PyObject *result = NULL;
    char *processed_data;
    size_t processed_len;
    const char *data;
    Py_ssize_t data_len;

    /* Parse the bytes object */
    if (!PyArg_ParseTuple(args, "O", &bytes_obj)) {
        return NULL;
    }

    /* Make sure it's bytes */
    if (!PyBytes_Check(bytes_obj)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be bytes");
        return NULL;
    }

    /* Get the bytes data */
    data = PyBytes_AsString(bytes_obj);
    data_len = PyBytes_Size(bytes_obj);

    /* Process the data */
    processed_data = process_buffer((const unsigned char*)data, data_len, &processed_len);
    if (!processed_data) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory for result");
        return NULL;
    }

    /* Create a new bytes object with the processed data */
    result = PyBytes_FromStringAndSize(processed_data, processed_len);
    
    /* Clean up */
    free(processed_data);
    
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