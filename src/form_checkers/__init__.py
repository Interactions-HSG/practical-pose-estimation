
#Define the __all__ variable to specify the public interface of the form_checkers package
__all__ = ['squat_formChecker', 'barbell_bentOver_formChecker', 'benchpress_formChecker']

#Import the submodules to make them accessible when the package is imported
from . import squat_formChecker
from . import barbell_bentOver_formChecker
from . import benchpress_formChecker