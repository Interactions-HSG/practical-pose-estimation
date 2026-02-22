
#Define the __all__ variable to specify the public interface of the form_checkers package
__all__ = [
    'SquatFormChecker',
	'BentOverRowFormChecker',
	'BenchpressFormChecker'
    ]

#Import the submodules to make them accessible when the package is imported
from .squat_formChecker import SquatFormChecker
from .bentOver_FormChecker import BentOverRowFormChecker
from .benchpress_formChecker import BenchpressFormChecker
