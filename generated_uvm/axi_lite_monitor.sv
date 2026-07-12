class axi_lite_monitor extends uvm_monitor;

    virtual axi_lite_if vif;
    uvm_analysis_port #(axi_lite_seq_item) ap;

    `uvm_component_utils(axi_lite_monitor)

    function new(string name = "axi_lite_monitor", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual axi_lite_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "monitor_run" %}
        axi_lite_seq_item tx;
        forever begin
            @(posedge vif.clk);
            tx = axi_lite_seq_item::type_id::create("tx");
            tx.awaddr = vif.cb.awaddr;
            tx.awvalid = vif.cb.awvalid;
            tx.awready = vif.cb.awready;
            tx.wdata = vif.cb.wdata;
            tx.wvalid = vif.cb.wvalid;
            tx.wready = vif.cb.wready;
            tx.bresp = vif.cb.bresp;
            tx.bvalid = vif.cb.bvalid;
            tx.bready = vif.cb.bready;
            ap.write(tx);
        end
// {% endllm_fill %}
    endtask

endclass