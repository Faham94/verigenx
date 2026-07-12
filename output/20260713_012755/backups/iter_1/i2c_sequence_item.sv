class i2c_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit scl;
    rand bit sda;
// {% endllm_fill %}

    `uvm_object_utils_begin(i2c_seq_item)
        // {% llm_fill "field_macros" %}
    `uvm_field_int(scl, UVM_ALL_ON)
    `uvm_field_int(sda, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "i2c_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Randomization constraints
// {% endllm_fill %}

endclass