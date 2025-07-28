# Questions
_Last update: June 17/25

A document to capture various in-flight questions as the project matures / efficiency tooling is introduced to speed up development efforts


## How to manage AI-contributed code?
- What mental approaches need to change when prompting / approving AI-generated code instead of writing it yourself? (_e.g. it becomes easier to hit "accept" without actively reading all code_).
- How do we highlight that some commits are inherently more risky because they've been written by the machine rather than human?
- Should some design patterns change because the LLM no longer makes this painful?
    - Example: Wave-Lite Redis module is implemented with complex object rather than individual fields because I found it a pain to retrofit two `variables.tf` files, the module call itself, and then the module's `main.tf`. AI can do most of these updates in a blink (_assumption: does it correctly_). Can we reduce object complexity in favour of more boilerplate if the boilerplate doesn't have to be written by a human?
- How should direction be given to an AI for module CHANGELOG / README updates if several rounds of conversation (_and resulting file modifications_) occurred within a single development effort? 


## General Design
- Legacy code has several multi-chained ternary checks with complex variables. Hard to grok when you first come back. Is it worth adding more lines of code to simply these constructs?
    - If we agree to simplify, how should the supporting variables be named?

    ```terraform
    # Full names with qualifier -- mirrors top-level variables at cost of long lines (potentially too verbose)
    wave_lite_redis_url_local    = "redis://wave-redis:6379"
    wave_lite_redis_url_remote   = "rediss://${var.elasticache_wave_lite[0].url}"
    wave_lite_redis_url          = var.flag_create_external_redis ? local.wave_lite_redis_url_local : local.wave_lite_redis_url_remote


    # Shortened helper variables. Resulting line is more sparse but relationship is more visual now. Potentially less
    # over-write risk if doing global find-replace now.
    wl_redis_local      = "redis://wave-redis:6379"
    wl_redis_remote     = "rediss://${var.elasticache_wave_lite[0].url}"
    wave_lite_redis_url = var.flag_create_external_redis ? local.wl_redis_remote : local.wl_redis_local
    ```


## Testing
- We need more robust automated testing, how can this be implemented? (_[Linked Issue](https://github.com/seqeralabs/cx-field-tools-installer/issues/49)_)
    - This is particularly relevant if we want to include more go-forward AI contributions.