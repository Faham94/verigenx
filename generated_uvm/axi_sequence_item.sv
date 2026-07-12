class axi_seq_item extends uvm_sequence_item;

    // {% llm_fill "transaction_fields" %}
    rand bit [31:0] awaddr;
    rand bit awvalid;
    rand bit awready;
    rand bit [31:0] wdata;
    rand bit wvalid;
    rand bit wready;
    rand bit [1:0] bresp;
    rand bit bvalid;
    rand bit bready;
    rand bit clock;
    rand bit write;
// {% endllm_fill %}

    `uvm_object_utils_begin(axi_seq_item)
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
    `uvm_field_int(clock, UVM_ALL_ON)
    `uvm_field_int(write, UVM_ALL_ON)
// {% endllm_fill %}
    `uvm_object_utils_end

    function new(string name = "axi_seq_item");
        super.new(name);
    endfunction

    // {% llm_fill "constraints" %}
    // Randomization constraints
    constraint c_awaddr_val { awaddr < 1073741824; }
    constraint c_awvalid_dist { awvalid dist { 0 := 30, 1 := 70 }; }
    constraint c_awready_dist { awready dist { 0 := 30, 1 := 70 }; }
    constraint c_wdata_val { wdata < 1073741824; }
    constraint c_wvalid_dist { wvalid dist { 0 := 30, 1 := 70 }; }
    constraint c_wready_dist { wready dist { 0 := 30, 1 := 70 }; }
    constraint c_bresp_range { bresp <= 3; }
    constraint c_bvalid_dist { bvalid dist { 0 := 30, 1 := 70 }; }
    constraint c_bready_dist { bready dist { 0 := 30, 1 := 70 }; }
// {% endllm_fill %}

endclass