class uart_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit [7:0] tx_data;
    rand bit [7:0] rx_data;
// {% endllm_fill %}

    `uvm_object_utils_begin(uart_seq_item)
        // {% llm_fill "field_macros" %}
    `uvm_field_int(tx_data, UVM_ALL_ON)
    `uvm_field_int(rx_data, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "uart_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Randomization constraints
    constraint c_tx_data_range { tx_data <= 255; }
    constraint c_rx_data_range { rx_data <= 255; }
// {% endllm_fill %}

endclass