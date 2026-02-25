class InferenceBackendInitializationError(Exception):
    pass


class InferenceBackendRuntimeError(Exception):
    pass


class InferenceBackendValidationError(Exception):
    pass


class InferenceBackendLoadError(Exception):
    pass


class UnknownPreprocessorError(Exception):
    pass


class PreprocessorInitError(Exception):
    pass


class PreprocessorRuntimeError(Exception):
    pass
