class axi_lite_env extends uvm_env;

    axi_lite_agent agent;
    axi_lite_scoreboard scoreboard;
    axi_lite_coverage coverage;

    `uvm_component_utils(axi_lite_env)

    function new(string name = "axi_lite_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent = axi_lite_agent::type_id::create("agent", this);
        scoreboard = axi_lite_scoreboard::type_id::create("scoreboard", this);
        coverage = axi_lite_coverage::type_id::create("coverage", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        agent.monitor.ap.connect(scoreboard.item_export);
        agent.monitor.ap.connect(coverage.analysis_export);
    endfunction

endclass