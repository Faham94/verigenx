class i2c_env extends uvm_env;

    i2c_agent agent;
    i2c_scoreboard scoreboard;
    i2c_coverage coverage;

    `uvm_component_utils(i2c_env)

    function new(string name = "i2c_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent = i2c_agent::type_id::create("agent", this);
        scoreboard = i2c_scoreboard::type_id::create("scoreboard", this);
        coverage = i2c_coverage::type_id::create("coverage", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        agent.monitor.ap.connect(scoreboard.item_export);
        agent.monitor.ap.connect(coverage.analysis_export);
    endfunction

endclass