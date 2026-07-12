class axi_driver extends uvm_driver #(axi_seq_item);

    virtual axi_if vif;

    `uvm_component_utils(axi_driver)

    function new(string name = "axi_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual axi_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("DRV", "Failed to get virtual interface from config DB")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "driver_reset" %}
        vif.rst_n <= 0;
        #100;
        vif.rst_n <= 1;
// {% endllm_fill %}

        forever begin
            seq_item_port.get_next_item(req);
            // {% llm_fill "driver_drive_item" %}
        @(posedge vif.aclk);
            vif.cb.awaddr <= req.awaddr;
            vif.cb.awvalid <= req.awvalid;
            vif.cb.wdata <= req.wdata;
            vif.cb.wvalid <= req.wvalid;
            vif.cb.bready <= req.bready;
            vif.cb.clock <= req.clock;
            vif.cb.write <= req.write;
        #10;
// {% endllm_fill %}
            seq_item_port.item_done();
        end
    endtask

endclass