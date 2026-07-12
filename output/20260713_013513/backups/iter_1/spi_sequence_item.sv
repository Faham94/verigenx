class spi_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit mosi;
    rand bit miso;
    rand bit sclk;
    rand bit cs_n;
// {% endllm_fill %}

    `uvm_object_utils_begin(spi_seq_item)
        // {% llm_fill "field_macros" %}
    `uvm_field_int(mosi, UVM_ALL_ON)
    `uvm_field_int(miso, UVM_ALL_ON)
    `uvm_field_int(sclk, UVM_ALL_ON)
    `uvm_field_int(cs_n, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "spi_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Randomization constraints
// {% endllm_fill %}

endclass