class fifo_monitor extends uvm_monitor;

    virtual fifo_if vif;
    uvm_analysis_port #(fifo_seq_item) ap;

    `uvm_component_utils(fifo_monitor)

    function new(string name = "fifo_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual fifo_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "monitor_run" %}
        fifo_seq_item tx;
        forever begin
            @(posedge vif.clk);
            tx = fifo_seq_item::type_id::create("tx"); // fifo_seq_item replaced dynamically in caller
            tx.wr_en = vif.wr_en;
            tx.rd_en = vif.rd_en;
            tx.wr_data = vif.wr_data;
            tx.rd_data = vif.rd_data;
            tx.full = vif.full;
            tx.empty = vif.empty;
            ap.write(tx);
        end
// {% endllm_fill %}
    endtask

endclass