# Task attributes

The task creation method returns a `Task^` entity. It is identified
by a unique
identifier named `id` that is generated by Taipy.
A task also holds various properties accessible as an attribute of the task:

-   `task.config_id` is the id of the scenario configuration.
-   `task.function` is the function that will take data from input data nodes and return data that should go
    inside the output data nodes .
-   `task.input` is the list of input data nodes.
-   `task.output` is the list of output data nodes.

!!! Example

    ```python linenums="1"
    import taipy as tp
    from config import \*

    scenario = tp.create_scenario(monthly_scenario_cfg)
    task = scenario.predicting

    # the config_id is an attribute of the task and equals "task_configuration"
    task.config_id

    # the function which is going to be executed with input data nodes and return value on output data nodes.
    task.function # predict

    # input is the list of input data nodes of the task
    task.input # [trained_model_cfg, current_month_cfg]

    # output is the list of input data nodes of the task
    task.output # [trained_model_cfg]

    # the current_month data node entity is exposed as an attribute of the task
    current_month_data_node = task.current_month
    ```

Taipy exposes multiple methods to manage the various tasks.

# Get Tasks

The first method to get a job is from its id by using the `taipy.get^` method

```python linenums="1"
import taipy as tp
from taipy.core.scheduler.scheduler import Scheduler
from config import *

scenario = tp.create_scenario(monthly_scenario_cfg)
task = scenario.predicting
task_retrieved = tp.get(task)
# task == task_retrieved
```

On the previous code, the two variables `task` and `task_retrieved` are equals.

A task can also be retrieved from a scenario or a pipeline, by accessing the task config_id attribute.

```python linenums="1"
task_1 = scenario.predicting
pipeline = scenario.sales
task_2 - pipeline.predicting
# task_1 == task_2
```

All the jobs can be retrieved using the method `taipy.get_tasks^`.

[:material-arrow-right: Next section show the data node management features](data-node-mgt.md).