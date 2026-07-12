class axi_lite_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit [31:0] awaddr;
    rand bit  awvalid;
    rand bit  awready;
    rand bit [31:0] wdata;
    rand bit  wvalid;
    rand bit  wready;
    rand bit [1:0] bresp;
    rand bit  bvalid;
    rand bit  bready;
// {% endllm_fill %}

    `uvm_object_utils_begin(axi_lite_seq_item)
        // {% llm_fill "field_macros" %}
    `uvm_field_int(awaddr, UVM_ALL_ON)
    `uvm_field_int(awvalid, UVM_ALL_ON)
    `uvm_field_int(awready, UVM_ALL_ON)
    `uvm_field_int(wdata, UVM_ALL_ON)
    `uvm_field_int(wvalid, UVM_ALL_ON)
    `uvm_field_int(wready, UVM_ALL_ON)
    `uvm_field_int(bresp, UVM_ALL_ON)
    `uvm_field_int(bvalid, UVM_ALL_ON)
    `uvm_field_int(bready, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "axi_lite_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Constraint blocks for transaction randomization
    // e.g., constraint c_valid { ... }
// {% endllm_fill %}

endclass