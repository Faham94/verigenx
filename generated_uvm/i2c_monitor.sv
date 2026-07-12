class i2c_monitor extends uvm_monitor;

    virtual i2c_if vif;
    uvm_analysis_port #(i2c_seq_item) ap;

    `uvm_component_utils(i2c_monitor)

    function new(string name = "i2c_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual i2c_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "monitor_run" %}
        i2c_seq_item tx;
        forever begin
            @(posedge vif.clk);
            tx = i2c_seq_item::type_id::create("tx");
            tx.scl = vif.scl;
            tx.sda = vif.sda;
            ap.write(tx);
        end
// {% endllm_fill %}
    endtask

endclass