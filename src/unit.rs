#[derive(Clone)]
#[allow(dead_code)]
pub enum TimeUnit {NS, US, MS, S}
#[derive(Clone)]
#[allow(dead_code)]
pub enum MemoryUnit {B, KB, KIB, MB, MIB, GB, GIB}
#[derive(Clone)]
#[allow(dead_code)]
pub enum PureUnit {Percentage, NoUnit}

#[derive(Clone)]
#[allow(dead_code)]
pub enum Unit {TimeUnit(TimeUnit), MemoryUnit(MemoryUnit), PureUnit(PureUnit)}

#[allow(dead_code)]
impl Unit {
    pub fn from_str(string: &str) -> Self {
        match string {
            "ns" => Unit::TimeUnit(TimeUnit::NS),
            "us" => Unit::TimeUnit(TimeUnit::US),
            "ms" => Unit::TimeUnit(TimeUnit::MS),
            "s" => Unit::TimeUnit(TimeUnit::S),

            "b" => Unit::MemoryUnit(MemoryUnit::B),
            "kb" => Unit::MemoryUnit(MemoryUnit::KB),
            "Mb" => Unit::MemoryUnit(MemoryUnit::MB),
            "Gb" => Unit::MemoryUnit(MemoryUnit::GB),
            "kib" => Unit::MemoryUnit(MemoryUnit::KIB),
            "Mib" => Unit::MemoryUnit(MemoryUnit::MIB),
            "Gib" => Unit::MemoryUnit(MemoryUnit::GIB),

            "%" => Unit::PureUnit(PureUnit::Percentage),
            _ => Unit::PureUnit(PureUnit::NoUnit),
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Unit::TimeUnit(TimeUnit::NS) => "ns",
            Unit::TimeUnit(TimeUnit::US) => "us",
            Unit::TimeUnit(TimeUnit::MS) => "ms",
            Unit::TimeUnit(TimeUnit::S)  => "s",

            Unit::MemoryUnit(MemoryUnit::B)  => "b",
            Unit::MemoryUnit(MemoryUnit::KB) => "kb",
            Unit::MemoryUnit(MemoryUnit::MB) => "Mb",
            Unit::MemoryUnit(MemoryUnit::GB) => "Gb",
            Unit::MemoryUnit(MemoryUnit::KIB) => "kib",
            Unit::MemoryUnit(MemoryUnit::MIB) => "Mib",
            Unit::MemoryUnit(MemoryUnit::GIB) => "Gib",

            Unit::PureUnit(PureUnit::Percentage) => "%",
            Unit::PureUnit(PureUnit::NoUnit) => "",
        }
    }

    pub fn as_scaler(&self) -> f64 {
        match self {
            Unit::TimeUnit(TimeUnit::NS) => 1e0,
            Unit::TimeUnit(TimeUnit::US) => 1e3,
            Unit::TimeUnit(TimeUnit::MS) => 1e6,
            Unit::TimeUnit(TimeUnit::S)  => 1e9,

            Unit::MemoryUnit(MemoryUnit::B)   => 1e0,
            Unit::MemoryUnit(MemoryUnit::KB)  => 1e3,
            Unit::MemoryUnit(MemoryUnit::MB)  => 1e6,
            Unit::MemoryUnit(MemoryUnit::GB)  => 1e9,
            Unit::MemoryUnit(MemoryUnit::KIB) => 1024.0,
            Unit::MemoryUnit(MemoryUnit::MIB) => 1024.0*1024.0,
            Unit::MemoryUnit(MemoryUnit::GIB) => 1024.0*1024.0*1024.0,

            Unit::PureUnit(PureUnit::Percentage) => 1e0,
            Unit::PureUnit(PureUnit::NoUnit) => 1e0,
        }
    }

    pub fn same_unit_pattern(&self, other: &Unit) -> bool {
        match (self, other) {
            (Unit::MemoryUnit(_), Unit::MemoryUnit(_)) => true,
            (Unit::TimeUnit(_), Unit::TimeUnit(_)) => true,
            (Unit::PureUnit(_), Unit::PureUnit(_)) => true,
            (_, _) => false
        }
    }
}