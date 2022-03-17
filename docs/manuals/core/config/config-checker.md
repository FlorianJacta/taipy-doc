Taipy provides a checking mechanism to validate your configuration is correct.

You can trigger the check by calling:
```python linenums="1"
import taipy as tp

tp.check_configuration()
```

The `taipy.check_configuration^` method returns a collector of issues. Each issue corresponds to an inconsistency on
the configuration attached to an issue level (`INFO`, `WARNING`, `ERROR`). `taipy.check_configuration^` raises an
exception if at least one issue collected has the `ERROR` level.

Here is the list of the issues possibly returned by the checker:

- An `ERROR` issue is created if the `clean_entities_enabled` property is populated in the
`GlobalAppConfig^`
with a non-Boolean value.

- An `ERROR` issue is created if the `storage_type` and the `scope` properties of any
`DataNodeConfig^`
have not been provided with a correct value.

- Depending on the `storage_type` value of a
`DataNodeConfig^`,
an `ERROR` issue is created if a specific required properties is missing.

- An `ERROR` issue is created if one of the `inputs` and `outputs` parameters of a
`TaskConfig^`
does not correspond to a `DataNodeConfig`.

- A `WARNING` issue is created if a
`TaskConfig^` have no input and no output.

- An `ERROR` issue is created if the `function` parameter of a
`TaskConfig^`
is not a callable function.

- An `ERROR` issue is created if one of the `task` parameters of a
`PipelineConfig^`
does not correspond to a `TaskConfig`.

- A `WARNING` issue is created if a
`PipelineConfig^` have no task configuration
defined.

- An `ERROR` issue is created if one of the `pipeline` parameters of a
`ScenarioConfig^`
does not correspond to a `PipelineConfig`.

- A `WARNING` issue is created if a
`ScenarioConfig^` have no pipeline
configuration defined.

- An `ERROR` issue is created if the `frequency` parameter of a
`ScenarioConfig^`
has an incorrect `Frequency^` value.

- An `INFO` issue is created if a
`ScenarioConfig^` have no `comparator` defined.

- If the `JobConfig^` has been
  configured with multiple workers, an `ERROR` issue is created if an `in_memory` `DataNodeConfig^` is defined.


[:material-arrow-right: Next section presents advanced configuration](advanced-config.md).