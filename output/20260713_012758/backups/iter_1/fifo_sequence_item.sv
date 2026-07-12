class fifo_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit wr_en;
    rand bit rd_en;
    rand bit [7:0] wr_data;
    rand bit [7:0] rd_data;
    rand bit full;
    rand bit empty;
// {% endllm_fill %}

    `uvm_object_utils_begin(fifo_seq_item)
        // {% llm_fill "field_macros" %}
    `uvm_field_int(wr_en, UVM_ALL_ON)
    `uvm_field_int(rd_en, UVM_ALL_ON)
    `uvm_field_int(wr_data, UVM_ALL_ON)
    `uvm_field_int(rd_data, UVM_ALL_ON)
    `uvm_field_int(full, UVM_ALL_ON)
    `uvm_field_int(empty, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "fifo_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Randomization constraints
    constraint c_wr_data_range { wr_data <= 255; }
    constraint c_rd_data_range { rd_data <= 255; }
// {% endllm_fill %}

endclass